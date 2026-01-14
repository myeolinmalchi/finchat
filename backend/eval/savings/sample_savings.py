import asyncio
import json
import random
from collections import defaultdict
from datetime import datetime, timedelta
from typing import Any, Dict, List, Tuple, Optional

from motor.motor_asyncio import AsyncIOMotorCollection

from common.database import init_mongodb_client


def _normalize_id(doc: Dict[str, Any]) -> str:
    _id = doc.get("_id")
    try:
        return str(_id)
    except Exception:
        return f"{_id}"


def _strata_key(doc: Dict[str, Any]) -> Tuple[Any, Any, Any, str]:
    term = doc.get("term", {}) or {}
    interest_type = doc.get("interest_type", "fixed")
    earn_method = doc.get("earn_method", "fixed")
    event = "event" if doc.get("event") else "no_event"
    return (
        term.get("policy_type"),
        interest_type,
        earn_method,
        event,
    )


def _is_amount_range_edge(doc: Dict[str, Any]) -> bool:
    amount = doc.get("amount", {}) or {}
    if amount.get("policy_type") != "RANGE":
        return False
    return (amount.get("min_amount") is not None) or (amount.get("max_amount")
                                                      is not None)


def _is_tiered_base_rate(doc: Dict[str, Any]) -> bool:
    base = doc.get("base_interest_rate")
    return isinstance(base, list)


def _is_fixed_date_imminent(doc: Dict[str, Any], within_days: int = 60) -> bool:
    term = doc.get("term", {}) or {}
    if term.get("policy_type") != "FIXED_DATE":
        return False
    maturity = term.get("maturity_date")
    if not maturity:
        return False
    if isinstance(maturity, str):
        try:
            maturity = datetime.fromisoformat(maturity)
        except Exception:
            return False
    if not isinstance(maturity, datetime):
        return False
    return maturity <= (datetime.now() + timedelta(days=within_days))


def _json_default(o):
    if isinstance(o, datetime):
        return o.isoformat()
    try:
        return str(o)
    except Exception:
        return None


# ---------- 샘플링 코어 ----------
def _proportional_stratified_sample(docs: List[Dict[str, Any]], K: int,
                                    seed: int) -> List[Dict[str, Any]]:
    random.seed(seed)
    buckets: Dict[Tuple[Any, Any, Any, str], List[Dict[str, Any]]] = defaultdict(list)
    for d in docs:
        buckets[_strata_key(d)].append(d)

    N = len(docs)
    if N == 0 or K <= 0:
        return []

    alloc = {k: max(1, round(K * (len(v) / N))) for k, v in buckets.items()}

    sample: List[Dict[str, Any]] = []
    for k, items in buckets.items():
        n = min(alloc[k], len(items))
        sample.extend(random.sample(items, n))

    if len(sample) > K:
        sample = random.sample(sample, K)
    elif len(sample) < K:
        used = {_normalize_id(x) for x in sample}
        remain = [x for x in docs if _normalize_id(x) not in used]
        if remain:
            sample.extend(random.sample(remain, min(K - len(sample), len(remain))))
    return sample


def _pick_edge_cases(docs: List[Dict[str, Any]], m: int,
                     seed: int) -> List[Dict[str, Any]]:
    random.seed(seed + 7)
    if m <= 0 or not docs:
        return []

    range_amount = [d for d in docs if _is_amount_range_edge(d)]
    tiered = [d for d in docs if _is_tiered_base_rate(d)]
    imminent = [d for d in docs if _is_fixed_date_imminent(d, within_days=60)]

    target_a = m // 3
    target_b = m // 3
    target_c = m - target_a - target_b

    chosen: List[Dict[str, Any]] = []

    def take(pool: List[Dict[str, Any]], k: int):
        nonlocal chosen
        if not pool or k <= 0:
            return
        pool_ids = {_normalize_id(x) for x in chosen}
        cands = [x for x in pool if _normalize_id(x) not in pool_ids]
        k = min(k, len(cands))
        if k > 0:
            chosen.extend(random.sample(cands, k))

    take(range_amount, target_a)
    take(tiered, target_b)
    take(imminent, target_c)

    if len(chosen) < m:
        chosen_ids = {_normalize_id(x) for x in chosen}
        remain = [x for x in docs if _normalize_id(x) not in chosen_ids]
        k = min(m - len(chosen), len(remain))
        if k > 0:
            chosen.extend(random.sample(remain, k))

    return chosen[:m]


async def sample_savings_to_json(
    coll: AsyncIOMotorCollection,
    output_path: str,
    K: int = 144,
    edge_ratio: float = 0.10,
    seed: int = 42,
    projection: Optional[Dict[str, int]] = None,
) -> Dict[str, Any]:

    if projection is None:
        projection = {
            "_id": 1,
            "name": 1,
            "institution": 1,
            "targets": 1,
            "event": 1,
            "term": 1,
            "amount": 1,
            "interest_type": 1,
            "earn_method": 1,
            "base_interest_rate": 1,
            "preferential_rates": 1,
            "max_interest_rate": 1,
        }

    cursor = coll.find({}, projection=projection)
    docs: List[Dict[str, Any]] = await cursor.to_list(length=None)
    N = len(docs)

    if N == 0:
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump([], f, ensure_ascii=False, indent=2, default=_json_default)
        return {"total": 0, "sampled": 0, "path": output_path}

    K = min(K, N) if K > 0 else 0
    if K == 0:
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump([], f, ensure_ascii=False, indent=2, default=_json_default)
        return {"total": N, "sampled": 0, "path": output_path}

    base_sample = _proportional_stratified_sample(docs, K, seed)

    m = int(round(K * max(0.0, min(edge_ratio, 1.0))))
    if m > 0:
        base_ids = {_normalize_id(x) for x in base_sample}
        remain_pool = [x for x in docs if _normalize_id(x) not in base_ids]
        edge_cases = _pick_edge_cases(remain_pool, m, seed=seed)

        if edge_cases:
            trimmed = base_sample[:max(0, len(base_sample) - len(edge_cases))]
            trimmed_ids = {_normalize_id(x) for x in trimmed}
            edge_cases = [x for x in edge_cases if _normalize_id(x) not in trimmed_ids]
            sample = trimmed + edge_cases
        else:
            sample = base_sample
    else:
        sample = base_sample

    # 4) JSON 저장
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(sample, f, ensure_ascii=False, indent=2, default=_json_default)

    return {"total": N, "sampled": len(sample), "path": output_path}


async def main():
    _, db = init_mongodb_client()
    coll = db.get_collection("savings")
    result = await sample_savings_to_json(coll,
                                          output_path="./saving_sample.json",
                                          K=144,
                                          edge_ratio=0.10,
                                          seed=42)
    print(result)


if __name__ == "__main__":
    asyncio.run(main())
