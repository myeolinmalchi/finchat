from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Union

from uuid import UUID

from domains.saving.schemas import SavingSearchResult

Primitive = Union[str, int, float, bool, None]


def _enum_or_literal(v: Any) -> Primitive:
    """Enum·Literal → str, 그 외는 그대로."""
    if hasattr(v, "value"):  # Enum
        return str(v.value)
    if isinstance(v, (str, int, float, bool)) or v is None:
        return v
    return str(v)


def _uuid(v: Any) -> Primitive:
    return str(v) if isinstance(v, UUID) else v


def _flatten_term_policy(term) -> Dict[str, Primitive]:
    match term.policy_type:
        case "RANGE" | "FIXED_DURATION":
            return {
                "type": term.policy_type,
                "range": f"{term.min_term}-{term.max_term}",
                "unit": term.term_unit,
            }
        case "CHOICES":
            return {
                "type": term.policy_type,
                "choices": term.choices,
                "unit": term.term_unit,
            }
        case "FIXED_DATE":
            return {
                "type":
                    term.policy_type,
                "maturity_date":
                    term.maturity_date.isoformat() if isinstance(
                        term.maturity_date, datetime) else term.maturity_date,
            }
        case _:
            return {"type": term.policy_type}


def _flatten_amount_policy(amount) -> Dict[str, Primitive]:
    base = {"type": amount.policy_type, "unit": amount.amount_unit}
    if amount.policy_type == "RANGE":
        base |= {"range": f"{amount.min_amount}-{amount.max_amount}"}
    elif amount.policy_type == "CHOICES":
        base |= {"choices": amount.choices}
    elif amount.policy_type == "FIXED_AMOUNT":
        base |= {"fixed": amount.fixed_amount}
    return base


def _flatten_interest_rate(rate) -> List[Dict[str, Primitive]]:
    """단일 수치 혹은 단계별 리스트를 공통 포맷으로."""
    if isinstance(rate, (int, float)):
        return [{"term_range": "all", "rate": rate}]

    return [{
        "term_range": f"{tier.min_term}-{tier.max_term or '∞'}",
        "rate": tier.interest_rate,
    } for tier in rate]


def _flatten_pref_rates(prefs) -> List[Dict[str, Any]]:
    return [{
        "description": p.description,
        "rate_type": _enum_or_literal(p.rate_type),
        "tiers": [{
            "condition": t.condition,
            "rate": t.interest_rate
        } for t in p.tiers],
    } for p in prefs]


def saving_search_result_mapper(result: SavingSearchResult,
                                include_raw: bool = False) -> Dict[str, Any]:

    saving = result.product

    doc: Dict[str, Any] = {
        # Metadata
        "score": result.score,
        "interest": result.interest,
        "principal": result.principal,
        "base_rate_rank": result.base_rate_rank,
        "mid_rate_rank": result.mid_rate_rank,
        "max_rate_rank": result.max_rate_rank,

        # Data
        "id": _uuid(saving.id),
        "name": saving.name,
        "institution": _enum_or_literal(saving.institution),
        "term_policy": _flatten_term_policy(saving.term),
        "amount_policy": _flatten_amount_policy(saving.amount),
        "interest_type": _enum_or_literal(saving.interest_type),
        "earn_method": _enum_or_literal(saving.earn_method),
        "base_interest_rate": _flatten_interest_rate(saving.base_interest_rate),
        "preferential_rates": _flatten_pref_rates(saving.preferential_rates),
    }

    if include_raw:
        doc["raw"] = result.model_dump(mode="json", by_alias=True)

    return doc
