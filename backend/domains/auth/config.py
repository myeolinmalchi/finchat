from dataclasses import dataclass, field
from typing import List


@dataclass(frozen=True)
class AuthConfig:

    secret_key: str
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    refresh_token_expire_days: int = 14


@dataclass(frozen=True)
class KakaoOAuthConfig:

    client_id: str
    client_secret: str | None
    redirect_path: str
    scopes: List[str] = field(
        default_factory=lambda: ["profile_nickname", "profile_image", "account_email"])
    authorize_endpoint: str = "https://kauth.kakao.com/oauth/authorize"
    token_endpoint: str = "https://kauth.kakao.com/oauth/token"
    profile_endpoint: str = "https://kapi.kakao.com/v2/user/me"
    server_origin: str = "http://localhost:8899"  # API 서버 origin

    @property
    def redirect_uri(self) -> str:
        return self.server_origin.rstrip("/") + self.redirect_path
