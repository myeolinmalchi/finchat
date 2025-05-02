from typing import List, overload

from aiohttp import ClientSession
from dotenv import load_dotenv
import os

from pydantic import TypeAdapter
import requests

from common.asyncio import retry_async, retry_sync
from schemas.embed import EmbedResult, RerankResult

load_dotenv()

EMBED_URL = os.getenv("EMBED_URL")

es = TypeAdapter(List[EmbedResult] | EmbedResult)


@overload
def create_embedding(
    texts: str,
    chunking: bool = True,
    truncate: bool = True,
    html: bool = False,
) -> EmbedResult:
    pass


@overload
def create_embedding(
    texts: List[str],
    chunking: bool = True,
    truncate: bool = True,
    html: bool = False,
) -> List[EmbedResult]:
    pass


@retry_sync(delay=3)
def create_embedding(
    texts: str | List[str],
    chunking: bool = True,
    truncate: bool = True,
    html: bool = False,
) -> EmbedResult | List[EmbedResult]:

    body = {
        "inputs": texts,
        "chunking": chunking,
        "truncate": truncate,
        "html": html,
    }

    res = requests.post(f"{EMBED_URL}/embed", json=body)
    if res.status_code == 200:
        raw = res.content
        return es.validate_json(raw)

    raise Exception("텍스트 임베딩에 실패했습니다.")


@retry_async(delay=3)
async def create_embedding_async(
    texts: str | List[str],
    session: ClientSession,
    chunking: bool = True,
    truncate: bool = True,
    html: bool = True,
) -> EmbedResult | List[EmbedResult]:

    body = {
        "inputs": texts,
        "chunking": chunking,
        "truncate": truncate,
        "html": html,
    }

    async with session.post(f"{EMBED_URL}/embed", json=body) as res:
        if res.status == 200:
            raw = await res.read()
            return es.validate_json(raw)

        raise Exception("텍스트 임베딩에 실패했습니다.")


rs = TypeAdapter(List[RerankResult])


@retry_async(delay=3)
async def rerank_async(
    query: str,
    texts: List[str],
    session: ClientSession,
    truncate: bool = True,
    truncation_direction="Right",
) -> List[RerankResult]:
    if not texts:
        return []

    body = {
        "query": query,
        "texts": texts,
        "truncate": truncate,
        "truncation_direction": truncation_direction,
    }

    async with session.post(f"{EMBED_URL}/rerank", json=body) as res:
        if res.status == 200:
            raw = await res.read()
            return rs.validate_json(raw)

        raise Exception("Failed Reranking")
