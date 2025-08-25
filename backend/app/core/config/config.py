import os
from dataclasses import dataclass

from domains.auth.config import AuthConfig, KakaoOAuthConfig
from domains.user.config import UserServiceConfig

from .mongo import MongoConfig
from .chroma import ChromaConfig


@dataclass(frozen=True)
class AppConfig:

    mongo: MongoConfig
    chroma: ChromaConfig

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
            chroma=ChromaConfig(),
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
