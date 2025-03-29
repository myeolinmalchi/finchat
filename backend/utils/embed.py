from typing import List, overload

from dotenv import load_dotenv
import os

from pydantic import TypeAdapter
import requests

from schemas.embed import EmbedResult

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

    raise Exception
