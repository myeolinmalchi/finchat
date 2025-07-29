from typing import Any, Callable, Dict, Type, TypeVar, cast
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from app.core.config import AppConfig

T = TypeVar("T")


class AppContainer:

    def __init__(self) -> None:
        self._factories: Dict[Type[Any], tuple[Callable[[AppContainer], Any],
                                               bool]] = {}
        self._singletons: Dict[Type[Any], Any] = {}

    def register(
        self,
        key: Type[T],
        factory: Callable[["AppContainer"], T],
        *,
        singleton: bool = True,
    ) -> None:
        self._factories[key] = (factory, singleton)

    def register_instance(self, key: Type[T], instance: T) -> None:
        self._singletons[key] = instance
        self._factories[key] = (lambda _: instance, True)

    def override(self,
                 key: Type[T],
                 factory: Callable[["AppContainer"], T],
                 *,
                 singleton: bool = True) -> None:
        self._factories[key] = (factory, singleton)
        if key in self._singletons:
            del self._singletons[key]

    def clear_singletons(self) -> None:
        self._singletons.clear()

    def resolve(self, key: Type[T]) -> T:
        if key in self._singletons:
            return cast(T, self._singletons[key])

        if key in self._factories:
            factory, singleton = self._factories[key]
            instance = factory(self)
            if singleton:
                self._singletons[key] = instance
            return cast(T, instance)

        for t, (factory, singleton) in self._factories.items():
            if issubclass(t, key):
                instance = factory(self)
                if singleton:
                    self._singletons[t] = instance
                return cast(T, instance)

        raise ValueError(f"{key.__name__}가 컨테이너에 등록되어 있지 않습니다.")
