import asyncio, json
from pathlib import Path
from typing import List

from motor.motor_asyncio import AsyncIOMotorCollection
import uvloop
from openai import AsyncOpenAI

from common.database import init_mongodb_client
from domains.saving.models import Saving

from domains.saving.repositories.mutations import insert_savings
from domains.saving.scrapers.parsers import (
    parse_term_policy,
    parse_amount_policy,
)

from domains.saving.scrapers.extractors import (
    extract_base_interest_rate_tiers,
    extract_saving_preferential_rates,
)

import os
import asyncio
from dotenv import load_dotenv

load_dotenv()


async def raw2saving(raw: dict, client: AsyncOpenAI) -> Saving:

    data = {
        "name": raw["basic_info"]["title"],
        "institution": raw["basic_info"]["institution"]
    }

    tasks = {}

    tasks["term"] = asyncio.create_task(
        parse_term_policy(raw["product_guide"]["term"], client=client))
    tasks["amount"] = asyncio.create_task(
        parse_amount_policy(raw["product_guide"]["term"], client=client))

    if hasattr(raw["interest_rate_guide"], "interest_rate_per_terms"):
        html_table = raw["interest_rate_guide"]["interest_rate_per_terms"]
        tasks["base_interest_rate"] = asyncio.create_task(
            extract_base_interest_rate_tiers(client, html_table))

    else:
        raw_interest_rate: str = raw["basic_info"]["base_interest_rate"]
        data["base_interest_rate"] = float(raw_interest_rate.lstrip("연").rstrip("%"))

    cond_text = "\n".join(raw["interest_rate_guide"]["conditions"])
    tasks["preferential_rates"] = asyncio.create_task(
        extract_saving_preferential_rates(client, cond_text))

    raw_interest_type = raw["interest_rate_guide"].get("interest_type", "고정금리")
    data["interest_type"] = "fixed" if raw_interest_type == "고정금리" else "variable"

    data["earn_method"] = "fixed"

    data = {**data, **{key: await task for key, task in tasks.items()}}

    return Saving(**data)


UPSTAGE_API_KEY = os.getenv("UPSTAGE_API_KEY", "")

INPUT_PATH = Path("data/savings.jsonl")
OUTPUT_PATH = Path("data/savings_parsed.jsonl")
MODEL = "solar-pro"
MAX_CONCURRENCY = 5


async def parse_raw_datas(openai_client: AsyncOpenAI):

    sem = asyncio.Semaphore(MAX_CONCURRENCY)

    raw_datas = []
    with open(INPUT_PATH, "r", encoding="utf-8") as fp:
        for line in fp:
            raw_datas.append(line)

    async def convert(line: str) -> Saving:
        raw = json.loads(line, strict=False)
        async with sem:
            return await raw2saving(raw, openai_client)

    savings: List[Saving] = await asyncio.gather(*(convert(data) for data in raw_datas))

    #result = await insert_savings(saving_collection, savings)

    with open(OUTPUT_PATH, "w", encoding="utf-8") as fp:
        for saving in savings:
            json_str = saving.model_dump_json()
            fp.write(json_str + "\n")


async def insert_datas(saving_collection: AsyncIOMotorCollection,):

    raw_datas: List[str] = []
    with open(OUTPUT_PATH, "r", encoding="utf-8") as fp:
        for line in fp:
            raw_datas.append(line)

    def convert(line: str) -> Saving:
        raw = json.loads(line, strict=False)
        return Saving(**raw)

    savings: List[Saving] = list(map(convert, raw_datas))
    result = await insert_savings(saving_collection, savings)

    print(f"{len(result['ids'])} rows added")


if __name__ == "__main__":
    uvloop.install()

    client, database = init_mongodb_client()

    openai_client = AsyncOpenAI(
        api_key=UPSTAGE_API_KEY,
        base_url="https://api.upstage.ai/v1",
    )

    saving_collection = database.get_collection("savings")
    #asyncio.run(parse_raw_datas(openai_client))
    asyncio.run(insert_datas(saving_collection))
