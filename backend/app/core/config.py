import os
from dataclasses import dataclass, field
from typing import Optional

from dotenv import load_dotenv
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase

from domains.auth.config import AuthConfig, KakaoOAuthConfig
from domains.user.config import UserServiceConfig

load_dotenv()


@dataclass(frozen=True)
class MongoCollections:

    users: str = field(default_factory=lambda: os.getenv("COL_USERS", "users"))
    tokens: str = field(default_factory=lambda: os.getenv("COL_TOKENS", "tokens"))
    social_accounts: str = field(
        default_factory=lambda: os.getenv("COL_SOCIAL_ACCOUNTS", "social_accounts"))
    tickets: str = field(
        default_factory=lambda: os.getenv("COL_LOGIN_TICKETS", "login_tickets"))

    chats: str = field(default_factory=lambda: os.getenv("COL_CHATS", "chats"))


@dataclass(frozen=True)
class MongoConfig:

    host: str
    port: str
    user: str
    pwd: str
    dbname: str
    auth_source: Optional[str] = None

    collections: MongoCollections = MongoCollections()

    @property
    def uri(self) -> str:
        auth_db = self.auth_source or self.dbname
        if self.user and self.pwd:
            return f"mongodb://{self.user}:{self.pwd}@{self.host}:{self.port}/{self.dbname}?authSource={auth_db}"
        return f"mongodb://{self.host}:{self.port}/{self.dbname}"

    def connect(self) -> AsyncIOMotorDatabase:
        client = AsyncIOMotorClient(self.uri)
        db = client.get_database(self.dbname)
        return db


@dataclass(frozen=True)
class AppConfig:

    mongo: MongoConfig
    auth: AuthConfig
    user: UserServiceConfig
    kakao: KakaoOAuthConfig

    @classmethod
    def from_env(cls) -> "AppConfig":
        return cls(
            mongo=MongoConfig(
                host=os.getenv("MONGODB_HOST", "localhost"),
                port=os.getenv("MONGODB_PORT", "27017"),
                user=os.getenv("MONGODB_USER", ""),
                pwd=os.getenv("MONGODB_PWD", ""),
                dbname=os.getenv("MONGODB_DBNAME", "app"),
            ),
            auth=AuthConfig(
                secret_key=os.getenv("JWT_SECRET_KEY", "dev-secret"),
                algorithm=os.getenv("JWT_ALGORITHM", "HS256"),
                access_token_expire_minutes=int(
                    os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", 30)),
                refresh_token_expire_days=int(os.getenv("REFRESH_TOKEN_EXPIRE_DAYS",
                                                        14)),
            ),
            user=UserServiceConfig(
                client_origin=os.getenv("CLIENT_ORIGIN", "http://localhost:5173"),
                signup_redirect_path=os.getenv("SIGNUP_REDIRECT_PATH", "/login"),
            ),
            kakao=KakaoOAuthConfig(
                client_id=os.getenv("KAKAO_REST_API_KEY", ""),
                client_secret=os.getenv("KAKAO_CLIENT_SECRET"),
                redirect_path=os.getenv("KAKAO_REDIRECT_PATH",
                                        "/api/v1/auth/kakao/callback"),
                server_origin=os.getenv("SERVER_ORIGIN", "http://localhost:8899"),
            ),
        )
