from typing import Optional, List
from motor.motor_asyncio import AsyncIOMotorCollection

from common.database import init_mongodb_client
from domains.saving.schemas import (
    SavingRateWeights,
    SavingSearchResult,
    TotalSavingSearchResult,
)

import math


def _create_score_pipeline(total_term_months: int, weights: SavingRateWeights):
    """적금 상품 score 계산 파이프라인"""

    pipeline = []

    base_interest_filter = {
        "$let": {
            "vars": {
                "tier": {
                    "$first": {
                        "$filter": {
                            "input": "$base_interest_rate",
                            "as": "t",
                            "cond": {
                                "$and": [{
                                    "$lte": ["$$t.min_term", total_term_months]
                                }, {
                                    "$or": [{
                                        "$eq": ["$$t.max_term", None]
                                    }, {
                                        "$gt": ["$$t.max_term", total_term_months]
                                    }]
                                }]
                            }
                        }
                    }
                }
            },
            "in": "$$tier.interest_rate"
        }
    }

    # 기본금리
    base_interest_rate = {
        "baseInterestRate": {
            "$cond": {
                "if": {
                    "$eq": [{
                        "$type": "$base_interest_rate"
                    }, "array"]
                },
                "then": base_interest_filter,
                "else": "$base_interest_rate"
            }
        }
    }

    # user_choice 우대금리 합
    total_user_choice_preferential_rate = {
        "totalUserChoicePreferentialRate": {
            "$sum": {
                "$map": {
                    "input": {
                        "$filter": {
                            "input": "$preferential_rates",
                            "as": "pr",
                            "cond": {
                                "$eq": ["$$pr.rate_type", "user_choice"]
                            },
                        }
                    },
                    "as": "uc",
                    "in": {
                        "$reduce": {
                            "input": "$$uc.tiers",
                            "initialValue": 0,
                            "in": {
                                "$cond": [
                                    {
                                        "$gt": ["$$this.interest_rate", "$$value"]
                                    },
                                    "$$this.interest_rate",
                                    "$$value",
                                ]
                            },
                        }
                    },
                }
            }
        }
    }

    # 전체 우대금리 합
    total_preferential_rate = {
        "totalPreferentialRate": {
            "$sum": {
                "$map": {
                    "input": "$preferential_rates",
                    "as": "pr",
                    "in": {
                        "$reduce": {
                            "input": "$$pr.tiers",
                            "initialValue": 0,
                            "in": {
                                "$cond": [
                                    {
                                        "$gt": ["$$this.interest_rate", "$$value"]
                                    },
                                    "$$this.interest_rate",
                                    "$$value",
                                ]
                            },
                        }
                    },
                }
            }
        }
    }

    pipeline += [{
        "$addFields": base_interest_rate
    }, {
        "$addFields": {
            **total_preferential_rate,
            **total_user_choice_preferential_rate
        }
    }]

    pipeline.append({
        "$addFields": {
            "maxPreferentialRate": {
                "$add": ["$baseInterestRate", "$totalPreferentialRate"]
            },
            "midPreferentialRate": {
                "$add": ["$baseInterestRate", "$totalUserChoicePreferentialRate"]
            },
            "score": {
                "$add": [{
                    "$multiply": ["$baseInterestRate", weights.base]
                }, {
                    "$multiply": [{
                        "$add": ["$baseInterestRate", "$totalPreferentialRate"]
                    }, weights.max]
                }, {
                    "$multiply": [{
                        "$add": [
                            "$baseInterestRate", "$totalUserChoicePreferentialRate"
                        ]
                    }, weights.intermediate]
                }]
            },
        }
    })

    pipeline.append({"$sort": {"score": -1}})

    return pipeline


def build_pipeline(
    weights: SavingRateWeights,
    target_amount: Optional[int] = None,
    monthly_deposit: Optional[int] = None,
    total_term_months: Optional[int] = None,
    top_k: int = 5,
    offset: int = 0,
):

    base_pipeline = _create_score_pipeline(
        total_term_months=total_term_months or 0,
        weights=weights,
    )

    extra = []

    # (1) 목표금액 + 월납입액 → 기간 계산 & 기간 정책 필터
    if target_amount is not None and monthly_deposit is not None:
        extra += [
            {
                "$addFields": {
                    "calcTermMonths": math.ceil(target_amount / monthly_deposit)
                }
            },
            {
                "$match": {
                    "$expr": {
                        "$switch": {
                            "branches": [
                                # RANGE
                                {
                                    "case": {
                                        "$eq": ["$term.policy_type", "RANGE"]
                                    },
                                    "then": {
                                        "$and": [
                                            {
                                                "$lte": [
                                                    "$term.min_term", "$calcTermMonths"
                                                ]
                                            },
                                            {
                                                "$or": [
                                                    {
                                                        "$eq": ["$term.max_term", None]
                                                    },
                                                    {
                                                        "$gte": [
                                                            "$term.max_term",
                                                            "$calcTermMonths"
                                                        ]
                                                    },
                                                ]
                                            },
                                        ]
                                    },
                                },
                                # CHOICES
                                {
                                    "case": {
                                        "$eq": ["$term.policy_type", "CHOICES"]
                                    },
                                    "then": {
                                        "$in": [
                                            "$calcTermMonths",
                                            {
                                                "$ifNull": ["$term.choices", []]
                                            },
                                        ]
                                    },
                                },
                                # FIXED_DURATION
                                {
                                    "case": {
                                        "$eq": ["$term.policy_type", "FIXED_DURATION"]
                                    },
                                    "then": {
                                        "$eq": ["$term.min_term", "$calcTermMonths"],
                                    },
                                },
                            ],
                            "default": True,
                        }
                    }
                }
            },
        ]

    # (2) 목표금액 + 기간 → 월납입액 계산 & 금액 정책 필터
    if target_amount is not None and total_term_months is not None:
        extra += [
            {
                "$addFields": {
                    "calcMonthlyDeposit": math.ceil(target_amount / total_term_months)
                }
            },
            {
                "$match": {
                    "$expr": {
                        "$switch": {
                            "branches": [
                                # RANGE
                                {
                                    "case": {
                                        "$eq": ["$amount.policy_type", "RANGE"]
                                    },
                                    "then": {
                                        "$and": [
                                            {
                                                "$lte": [
                                                    "$amount.min_amount",
                                                    "$calcMonthlyDeposit"
                                                ]
                                            },
                                            {
                                                "$or": [
                                                    {
                                                        "$eq": [
                                                            "$amount.max_amount", None
                                                        ]
                                                    },
                                                    {
                                                        "$gte": [
                                                            "$amount.max_amount",
                                                            "$calcMonthlyDeposit"
                                                        ]
                                                    },
                                                ]
                                            },
                                        ]
                                    },
                                },
                                # CHOICES
                                {
                                    "case": {
                                        "$eq": ["$amount.policy_type", "CHOICES"]
                                    },
                                    "then": {
                                        "$in": [
                                            "$calcMonthlyDeposit",
                                            {
                                                "$ifNull": ["$amount.choices", []]
                                            },
                                        ]
                                    },
                                },
                                # FIXED_AMOUNT
                                {
                                    "case": {
                                        "$eq": ["$amount.policy_type", "FIXED_AMOUNT"]
                                    },
                                    "then": {
                                        "$eq": [
                                            "$amount.fixed_amount",
                                            "$calcMonthlyDeposit"
                                        ]
                                    },
                                },
                            ],
                            "default": True,
                        }
                    }
                }
            },
        ]

    # (3) 월납입액 + 기간 → 만기 금액 시뮬레이션
    if monthly_deposit is not None and total_term_months is not None:
        extra += [
            {
                "$addFields": {
                    "principal": {
                        "$multiply": [monthly_deposit, total_term_months]
                    },
                    "interest": {
                        "$multiply": [
                            {
                                "$divide": [
                                    {
                                        "$multiply": [
                                            monthly_deposit,
                                            {
                                                "$add": [total_term_months, 1]
                                            },
                                            total_term_months,
                                        ]
                                    },
                                    24,
                                ]
                            },
                            {
                                "$divide": ["$maxPreferentialRate", 100]
                            },
                        ]
                    },
                }
            },
            {
                "$addFields": {
                    "maturityAmount": {
                        "$add": ["$principal", "$interest"]
                    }
                }
            },
        ]

    if monthly_deposit is not None and total_term_months is not None:
        extra += [
            {
                "$addFields": {
                    "principal": {
                        "$multiply": [monthly_deposit, total_term_months]
                    },
                    "interest": {
                        "$multiply": [
                            {
                                "$divide": [
                                    {
                                        "$multiply": [
                                            monthly_deposit,
                                            {
                                                "$add": [total_term_months, 1]
                                            },
                                            total_term_months,
                                        ]
                                    },
                                    24,
                                ]
                            },
                            {
                                "$divide": ["$maxPreferentialRate", 100]
                            },
                        ]
                    },
                }
            },
            {
                "$addFields": {
                    "maturityAmount": {
                        "$add": ["$principal", "$interest"]
                    }
                }
            },
        ]

    extra += [
        {
            "$setWindowFields": {                # 기본금리 랭킹
                "sortBy": {"baseInterestRate": -1},
                "output": {"base_rate_rank": {"$rank": {}}},
            }
        },
        {
            "$setWindowFields": {                # 중간금리 랭킹
                "sortBy": {"midPreferentialRate": -1},
                "output": {"mid_rate_rank": {"$rank": {}}},
            }
        },
        {
            "$setWindowFields": {                # 최대금리 랭킹
                "sortBy": {"maxPreferentialRate": -1},
                "output": {"max_rate_rank": {"$rank": {}}},
            }
        },
    ]

    if offset > 0:
        extra.append({"$skip": offset})

    extra.append({"$limit": top_k})

    return base_pipeline + extra


from pprint import pprint


async def find_savings(
    collection: AsyncIOMotorCollection,
    weights: SavingRateWeights,
    target_amount: Optional[int] = None,
    monthly_deposit: Optional[int] = None,
    total_term_months: Optional[int] = None,
    top_k: int = 5,
    offset: int = 0,
) -> List[SavingSearchResult]:

    pipeline = build_pipeline(weights=weights,
                              target_amount=target_amount,
                              monthly_deposit=monthly_deposit,
                              total_term_months=total_term_months,
                              top_k=top_k,
                              offset=offset)

    try:
        cursor = collection.aggregate(pipeline)
        raw_datas = await cursor.to_list()
        savings = [SavingSearchResult(**raw) for raw in raw_datas]

        return savings

    except Exception as e:
        raise RuntimeError("적금 검색에 실패했습니다.") from e


async def _test():

    _, db = init_mongodb_client()
    collection = db.get_collection("savings")

    weights = SavingRateWeights(base=0.3, max=0.2, intermediate=0.5)
    target_amount = 30_000_000
    monthly_deposit = 500_000
    #total_term_months = 12
    top_k = 5

    try:
        results = await find_savings(
            collection=collection,
            weights=weights,
            target_amount=target_amount,
            monthly_deposit=monthly_deposit,
            top_k=top_k,
        )

        print("적금 검색 결과:")
        for idx, result in enumerate(results, 1):
            pprint(f"{idx}. {result}\n\n")

    except Exception as e:
        print("테스트 실패:", e)


import asyncio

if __name__ == "__main__":
    asyncio.run(_test())
