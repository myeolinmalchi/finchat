from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from langchain_upstage import ChatUpstage
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.core.container import AppContainer, init_container

from app.api.v1 import router as v1_router
from domains.auth.services import TokenService
from domains.common.agents.supervisor import init_graph


def create_app(lifespan):
    """FastAPI 인스턴스 생성 및 초기화"""

    app = FastAPI(lifespan=lifespan)
    app.include_router(v1_router.router, prefix="/api/v1")

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    return app


@asynccontextmanager
async def lifespan(app: FastAPI):
    """FastAPI 인스턴스 생명주기 관리 함수"""

    llm = ChatUpstage(
        model="solar-pro2",
        temperature=0.0,
        reasoning_effort="low",
        max_tokens=16384,
    )

    container = await init_container()
    app.state.container = container

    database = container.resolve(AsyncIOMotorDatabase)
    app.state.graph = init_graph(llm, database)

    yield

    app.state.client.close()


app = create_app(lifespan)


@app.middleware("http")
async def verify_token_middleware(req: Request, call_next):

    container: AppContainer = req.app.state.container
    token_service: TokenService = container.resolve(TokenService)

    excluded_paths = [
        "/docs",
        "/openapi.json",
        "/api/v1/auth/kakao/callback",
        "/api/v1/auth/kakao/login",
        "/api/v1/auth/token/refresh",
        "/api/v1/auth/exchange",
    ]

    if req.method == "OPTIONS" or req.url.path in excluded_paths:
        response = await call_next(req)
        return response

    access_token = req.cookies.get("access_token")
    if not access_token:
        res = JSONResponse(status_code=status.HTTP_401_UNAUTHORIZED,
                           content={"detail": "Not authenticated"})
        res.delete_cookie("access_token")
        res.delete_cookie("refresh_token")
        return res

    try:
        payload = token_service.verify_and_decode_token(access_token)
        req.state.user_id = payload.get("sub")

    except Exception:
        res = JSONResponse(status_code=status.HTTP_401_UNAUTHORIZED,
                           content={"detail": "Token has expired or is invalid"})
        res.delete_cookie("access_token")
        res.delete_cookie("refresh_token")
        return res

    response = await call_next(req)
    return response
