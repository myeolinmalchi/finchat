from contextlib import asynccontextmanager
import json
from typing import List
from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from langchain_upstage import ChatUpstage
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.authorization import JWTAuthMiddleware
from app.db import init_db
from common.database import init_mongodb_client
from fastapi.security.api_key import APIKeyHeader

from app.api.v1 import router as v1_router

from common.database import init_mongodb_client
from fastapi.security.api_key import APIKeyHeader

from app.api.v1 import router as v1_router
from domains.common.agents.supervisor import init_graph
from domains.saving.models import Saving
from domains.saving.repositories.mutations import insert_savings


def create_app(lifespan):
    """FastAPI 인스턴스 생성 및 초기화"""

    auth_header = APIKeyHeader(name="Authorization", auto_error=False)
    app = FastAPI(lifespan=lifespan, dependencies=[Depends(auth_header)])

    app.include_router(v1_router.router, prefix="/api/v1")

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.add_middleware(JWTAuthMiddleware)

    init_db()

    return app


async def reset_database(database: AsyncIOMotorDatabase):

    saving_collection = database.get_collection("savings")
    delete_result = await saving_collection.delete_many({})
    print(delete_result)

    raw_datas: List[str] = []
    with open("data/savings_parsed.jsonl", "r", encoding="utf-8") as f:
        for line in f:
            raw_datas.append(line)

    def convert(line: str) -> Saving:
        raw = json.loads(line, strict=False)
        return Saving(**raw)

    savings: List[Saving] = list(map(convert, raw_datas))
    insert_result = await insert_savings(saving_collection, savings)
    print(insert_result)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """FastAPI 인스턴스 생명주기 관리 함수"""

    client, database = init_mongodb_client()
    app.state.client = client
    app.state.database = database

    await reset_database(database)

    llm = ChatUpstage(
        model="solar-pro2",
        temperature=0.0,
        reasoning_effort="low",
        max_tokens=16384,
    )

    app.state.graph = init_graph(llm, database)

    yield

    app.state.client.close()


app = create_app(lifespan)
