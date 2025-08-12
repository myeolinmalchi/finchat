from typing import Callable, Type, TypeVar
from fastapi import Depends, Request
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.core.container import AppContainer

T = TypeVar("T")


def get_container(request: Request) -> AppContainer:
    return request.app.state.container


def inject(dep_type: Type[T]) -> Callable[..., T]:

    def _resolver(container: AppContainer = Depends(get_container)) -> T:
        _instance = container.resolve(dep_type)
        if not _instance:
            raise ValueError(f"AppContainer에 {dep_type.__name__}이 존재하지 않습니다.")
        return _instance

    return _resolver


def get_database(request: Request) -> AsyncIOMotorDatabase:
    return request.app.container.db


def get_workflow_stream(request: Request):
    return request.app.state.graph
