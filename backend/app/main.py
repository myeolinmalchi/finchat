from contextlib import asynccontextmanager
from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware

from app.authorization import JWTAuthMiddleware
from app.db import init_db
from common.database import init_mongodb_client
from fastapi.security.api_key import APIKeyHeader

from app.api.v1 import router as v1_router

from common.database import init_mongodb_client
from fastapi.security.api_key import APIKeyHeader


from app.api.v1 import router as v1_router

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


@asynccontextmanager
async def lifespan(app: FastAPI):
    """FastAPI 인스턴스 생명주기 관리 함수"""

    client, database = init_mongodb_client()
    app.state.client = client
    app.state.database = database

    yield

    app.state.client.close()


app = create_app(lifespan)
