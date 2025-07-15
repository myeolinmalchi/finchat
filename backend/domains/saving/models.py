from datetime import datetime
from typing import List, Literal, Optional

from pydantic import BaseModel, Field

from domains.common.types import Institution, TermUnit

from .types import (
    SavingInterestType,
    SavingEarnMethod,
    SavingPreferentialRateType,
)

import uuid


class PreferentialRateTier(BaseModel):
    """우대금리 내의 개별 조건과 금리

    Attributes:
        condition (str): 상세 조건
        interest_rate (float): 우대금리
    """

    condition: str
    interest_rate: float


class SavingPreferentialRate(BaseModel):
    """적금 상품의 개별 우대금리 조건

    Attributes:
        description (str): 조건 설명
        rate_type (SavingPreferentialRateType): 우대금리 유형
        tiers (List[PreferentialRateTier]): 조건에 따른 상세 금리 목록
    """

    description: str
    rate_type: SavingPreferentialRateType
    tiers: List[PreferentialRateTier]


class BaseInterestRateTier(BaseModel):
    """가입 기간 구간별 기본 금리

    Attributes:
        min_term (int): 구간의 최소값 (ge)
        max_term (Optional[int]): 구간의 최대값 (lt)
        interest_rate (float): 해당 구간에 적용되는 연 금리 (%p)
    """

    min_term: int
    max_term: Optional[int] = None
    interest_rate: float


# 가입 기간 정책 유형
TermPolicyType = Literal["RANGE", "FIXED_DURATION", "CHOICES", "FIXED_DATE"]


class TermPolicy(BaseModel):
    """가입 기간 정책"""

    policy_type: TermPolicyType = Field(..., description="기간 정책 유형")

    # type: RANGE, FIXED_DURATION
    min_term: Optional[int] = None
    max_term: Optional[int] = None

    # type: CHOICES
    choices: Optional[List[int]] = None

    # type: RANGE, FIXED_DURATION, CHOICES
    term_unit: Optional[TermUnit] = None

    # type: FIXED_DATE
    maturity_date: Optional[datetime] = None


# 납입 금액 정책 유형 (Amount)
AmountPolicyType = Literal["RANGE", "CHOICES", "FIXED_AMOUNT"]


class AmountPolicy(BaseModel):
    """
    납입 금액 정책을 나타내는 데이터 모델
    """
    policy_type: AmountPolicyType = Field(..., description="금액 정책 유형")

    # 'RANGE' 유형에 사용
    min_amount: Optional[int] = None
    max_amount: Optional[int] = None

    # 'CHOICES' 유형에 사용
    choices: Optional[List[int]] = None

    # 'FIXED_AMOUNT' 유형에 사용
    fixed_amount: Optional[int] = None

    # 납입 주기 ('월', '일', '년')
    amount_unit: TermUnit = "month"


class Saving(BaseModel):
    """금융 기관의 단일 적금 상품 정보

    Attributes:
        id (str): 상품의 고유 식별자.

        name (str): 상품명.
        institution (Institution): 상품을 제공하는 기관.
        targets (str): 상품 가입 대상.

        event (str | None): 특판


        term (TermPolicy): 상품 가입 기간 관련 정책
        amount (AmountPolicy): 상품 납입 금액 관련 정책

        interest_type (SavingInterestType): 금리 유형 ('fixed', 'variable').
        earn_method (SavingEarnMethod): 적립 방식 ('fixed', 'flexible').
        enroll_method (str | None): 가입 방법.

        base_interest_rate (float | List[BaseInterestRateTier]): 기본금리
        preferential_rates (List[SavingPreferentialRate]): 우대금리
    """

    id: str = Field(alias="_id",
                    default_factory=lambda _: str(uuid.uuid4()),
                    frozen=True)

    name: str
    institution: Institution
    targets: str

    event: Optional[str] = None

    term: TermPolicy
    amount: AmountPolicy

    interest_type: SavingInterestType = "fixed"
    earn_method: SavingEarnMethod = "fixed"
    enroll_method: Optional[str] = None

    base_interest_rate: float | List[BaseInterestRateTier]
    preferential_rates: List[SavingPreferentialRate]
