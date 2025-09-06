from typing import Any, Callable, Dict, Type, TypeVar, cast

from motor.motor_asyncio import AsyncIOMotorDatabase

from app.core.config import AppConfig
from domains.auth.repositories import TokenRepository, TicketRepository
from domains.auth.services import KakaoOAuthService, TicketService, TokenService

from domains.auth.usecases import KakaoAuthUseCase
from domains.chat.repositories import ChatRepository
from domains.chat.services import ChatService
from domains.user.repositories import SocialRepository, UserMemoryRepository, UserRepository
from domains.user.services import UserMemoryService, UserService

from functools import lru_cache

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


@lru_cache
async def init_container() -> AppContainer:
    c = AppContainer()

    c.register(AppConfig, lambda _: AppConfig.from_env())

    def _db_factory(_c: AppContainer) -> AsyncIOMotorDatabase:
        cfg = _c.resolve(AppConfig)
        return cfg.mongo.connect()

    c.register(AsyncIOMotorDatabase, _db_factory)
    c.register(
        UserMemoryRepository,
        lambda _c: UserMemoryRepository(cfg=_c.resolve(AppConfig),
                                        db=_c.resolve(AsyncIOMotorDatabase)),
    )

    c.register(
        UserMemoryService,
        lambda _c: UserMemoryService(cfg=_c.resolve(AppConfig),
                                     memory_repo=_c.resolve(UserMemoryRepository),
                                     user_repo=_c.resolve(UserRepository)),
    )

    c.register(
        UserRepository, lambda _c: UserRepository(
            cfg=_c.resolve(AppConfig),
            db=_c.resolve(AsyncIOMotorDatabase),
        ))
    c.register(
        SocialRepository, lambda _c: SocialRepository(
            cfg=_c.resolve(AppConfig),
            db=_c.resolve(AsyncIOMotorDatabase),
        ))
    c.register(
        TokenRepository, lambda _c: TokenRepository(
            cfg=_c.resolve(AppConfig),
            db=_c.resolve(AsyncIOMotorDatabase),
        ))
    c.register(
        TicketRepository, lambda _c: TicketRepository(
            cfg=_c.resolve(AppConfig),
            db=_c.resolve(AsyncIOMotorDatabase),
        ))

    c.register(
        TicketService, lambda _c: TicketService(
            cfg=_c.resolve(AppConfig),
            ticket_repo=_c.resolve(TicketRepository),
        ))
    c.register(
        TokenService, lambda _c: TokenService(
            cfg=_c.resolve(AppConfig),
            token_repo=_c.resolve(TokenRepository),
        ))
    c.register(
        UserService, lambda _c: UserService(
            cfg=_c.resolve(AppConfig),
            user_repo=_c.resolve(UserRepository),
            social_repo=_c.resolve(SocialRepository),
        ))
    c.register(KakaoOAuthService,
               lambda _c: KakaoOAuthService(cfg=_c.resolve(AppConfig),))

    c.register(
        KakaoAuthUseCase, lambda _c: KakaoAuthUseCase(
            kakao_service=_c.resolve(KakaoOAuthService),
            user_service=_c.resolve(UserService),
            token_service=_c.resolve(TokenService),
            ticket_service=_c.resolve(TicketService),
        ))

    c.register(
        ChatRepository, lambda _c: ChatRepository(
            cfg=_c.resolve(AppConfig),
            db=_c.resolve(AsyncIOMotorDatabase),
        ))
    c.register(
        ChatService,
        lambda _c: ChatService(cfg=_c.resolve(AppConfig),
                               user_repo=_c.resolve(UserRepository),
                               memory_repo=_c.resolve(UserMemoryRepository),
                               chat_repo=_c.resolve(ChatRepository)))

    return c
