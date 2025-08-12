from dataclasses import dataclass
import hashlib
from typing import Any, Dict, Literal, Optional, TypedDict
from datetime import datetime, timedelta, timezone
from urllib.parse import urlencode
import uuid

import httpx
import jwt

from app.core.config import AppConfig

from domains.auth.repositories import TicketRepository, TokenRepository
from domains.user.models import Token


class InvalidTokenError(Exception):
    pass


TokenPair = TypedDict("TokenPair", {"access_token": str, "refresh_token": str})


class TokenService:

    def __init__(self, *, cfg: AppConfig, token_repo: TokenRepository):
        self.auth = cfg.auth
        self.token_repo = token_repo

    def _create_token(self, sub: str, expires_delta: timedelta) -> str:
        expire = datetime.now(timezone.utc) + expires_delta
        payload = {"exp": expire, "sub": sub}
        return jwt.encode(payload, self.auth.secret_key, algorithm=self.auth.algorithm)

    async def issue_new_token_pair(self, user_id: str) -> TokenPair:
        """액세스 토큰과 리프레시 토큰 쌍 발급 및 DB 저장"""

        access_token_expires = timedelta(minutes=self.auth.access_token_expire_minutes)
        refresh_token_expires = timedelta(days=self.auth.refresh_token_expire_days)

        at = self._create_token(user_id, access_token_expires)
        rt = self._create_token(user_id, refresh_token_expires)

        token_model = Token(
            user_id=user_id,
            access_token=at,
            refresh_token=rt,
            access_token_expires_at=datetime.now(timezone.utc) + access_token_expires,
            refresh_token_expires_at=datetime.now(timezone.utc) + refresh_token_expires)

        #await self.token_repo.upsert_tokens(token_model.model_dump())
        await self.token_repo.insert_token(token_model)

        return {"access_token": at, "refresh_token": rt}

    def verify_and_decode_token(self, token: str) -> Dict[str, Any]:
        try:
            return jwt.decode(token,
                              self.auth.secret_key,
                              algorithms=[self.auth.algorithm])
        except jwt.ExpiredSignatureError:
            raise
        except jwt.PyJWTError:
            raise InvalidTokenError("Invalid token")

    # TODO: Refresh Token Rotation 방식 적용 필요
    async def refresh_access_token(self, refresh_token: str) -> str:
        """
        리프레시 토큰으로 새로운 액세스 토큰 발급하고 DB 정보 갱신.
        이 함수가 만료 여부 판별 및 재발급/갱신을 모두 처리.
        """
        try:
            payload = self.verify_and_decode_token(refresh_token)
            user_id = payload["sub"]
        except jwt.ExpiredSignatureError:
            raise InvalidTokenError("Refresh token has expired")
        except InvalidTokenError:
            raise

        stored_token_info = await self.token_repo.get_tokens_by_refresh_token(
            refresh_token)
        if not stored_token_info:
            raise InvalidTokenError("Refresh token not found in DB or revoked")

        access_token_expires = timedelta(minutes=self.auth.access_token_expire_minutes)
        new_at = self._create_token(user_id, access_token_expires)

        update_data = {
            "access_token":
                new_at,
            "access_token_expires_at":
                datetime.now(timezone.utc) + access_token_expires,
        }

        await self.token_repo.upsert_tokens(user_id=user_id,
                                            refresh_token=refresh_token,
                                            new_data=update_data)

        return new_at

    async def logout(self,
                     *,
                     user_id: Optional[str] = None,
                     refresh_token: Optional[str] = None) -> bool:
        """
        DB에서 토큰 문서를 삭제하여 로그아웃 처리.
        둘 중 하나는 반드시 전달되어야 함.
        return: 실제 삭제가 일어났는지 여부
        """
        if not user_id and not refresh_token:
            raise ValueError("user_id 또는 refresh_token 중 최소 하나는 필요합니다.")

        deleted_count = await self.token_repo.delete_tokens(
            user_id=user_id,
            refresh_token=refresh_token,
        )
        return deleted_count > 0


@dataclass(frozen=True)
class KakaoTokenResponse:
    token_type: str
    access_token: str
    expires_in: int
    refresh_token: str
    refresh_token_expires_in: int
    id_token: Optional[str] = None
    scope: Optional[str] = None


@dataclass(frozen=True)
class KakaoUserInfoResponse:
    kakao_user_id: str
    email: str
    profile_image_url: Optional[str] = None
    nickname: Optional[str] = None


class KakaoOAuthService:

    def __init__(self, cfg: AppConfig):
        self.cfg = cfg.kakao

    @property
    def auth_url(self) -> str:
        """인가 코드 요청 URL"""

        params = {
            "response_type": "code",
            "client_id": self.cfg.client_id,
            "redirect_uri": self.cfg.redirect_uri,
            "scope": " ".join(self.cfg.scopes) if self.cfg.scopes else None,
        }

        print(self.cfg.redirect_uri)
        params = {k: v for k, v in params.items() if v is not None}
        return f"{self.cfg.authorize_endpoint}?{urlencode(params)}"

    async def get_kakao_token(self, code: str) -> KakaoTokenResponse:
        """인증 토큰 발급"""

        payload = {
            "grant_type": "authorization_code",
            "client_id": self.cfg.client_id,
            "redirect_uri": self.cfg.redirect_uri,
            "code": code,
        }
        if self.cfg.client_secret:
            payload["client_secret"] = self.cfg.client_secret

        headers = {"Content-Type": "application/x-www-form-urlencoded;charset=utf-8"}

        async with httpx.AsyncClient() as client:
            res = await client.post(self.cfg.token_endpoint,
                                    data=payload,
                                    headers=headers)
            res.raise_for_status()
            return KakaoTokenResponse(**res.json())

    async def get_user_info(self, access_token: str) -> Optional[KakaoUserInfoResponse]:
        """액세스 토큰 사용하여 사용자 정보 요청"""

        headers = {"Authorization": f"Bearer {access_token}"}
        async with httpx.AsyncClient() as client:
            res = await client.get(self.cfg.profile_endpoint, headers=headers)
            res.raise_for_status()
            data = res.json()

        kakao_account = data.get("kakao_account")
        if not kakao_account:
            return None

        profile = kakao_account.get("profile") or {}

        return KakaoUserInfoResponse(
            kakao_user_id=data["id"],
            email=kakao_account.get("email"),
            profile_image_url=profile.get("profile_image_url"),
            nickname=profile.get("nickname"),
        )


class TicketService:

    def __init__(self, *, cfg: AppConfig, ticket_repo: TicketRepository):
        self.cfg = cfg
        self.repo = ticket_repo

    async def issue_ticket(
        self,
        user_id: str,
        ttl_seconds: int = 60,
        ua_fingerprint: Optional[str] = None,
    ) -> str:
        raw_ticket = uuid.uuid4().hex
        ticket_hash = self._hash(raw_ticket)

        doc = {
            "ticket_hash": ticket_hash,
            "user_id": user_id,
            "ua_fingerprint": ua_fingerprint,
            "expires_at": datetime.now(timezone.utc) + timedelta(seconds=ttl_seconds),
        }
        await self.repo.insert(doc)
        return raw_ticket

    async def consume_ticket(
        self,
        raw_ticket: str,
        ua_fingerprint: Optional[str] = None,
    ) -> Optional[str]:
        ticket_hash = self._hash(raw_ticket)
        doc = await self.repo.find_one_and_delete(ticket_hash=ticket_hash,
                                                  ua_fingerprint=ua_fingerprint)
        return doc["user_id"] if doc else None

    @staticmethod
    def _hash(value: str) -> str:
        return hashlib.sha256(value.encode("utf-8")).hexdigest()


"""
async def run(user_id: str):
    client, db = init_mongodb_client()

    token_repo = TokenRepository(db)
    token_service = TokenService(token_repo)
    tokens = await token_service.issue_new_token_pair(user_id)
    print(tokens)


if __name__ == "__main__":
    temp = "e954ff6a-850a-4fab-a1e1-a7338876a275"
    asyncio.run(run(temp))
"""
