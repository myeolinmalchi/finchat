from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from domains.auth.services import KakaoOAuthService, TokenService, TicketService
from domains.user.services import UserService


@dataclass
class KakaoAuthResult:
    user_id: str
    raw_ticket: str
    redirect_url: str


class KakaoAuthUseCase:

    def __init__(self, kakao_service: KakaoOAuthService, user_service: UserService,
                 token_service: TokenService, ticket_service: TicketService):

        self.kakao_service = kakao_service
        self.user_service = user_service
        self.token_service = token_service
        self.ticket_service = ticket_service

    async def callback(self,
                       code: str,
                       *,
                       ua_fingerprint: Optional[str] = None,
                       ticket_ttl_seconds: int = 60) -> KakaoAuthResult:

        token_info = await self.kakao_service.get_kakao_token(code)
        kakao_user_info = await self.kakao_service.get_user_info(token_info.access_token
                                                                )

        if not kakao_user_info:
            raise ValueError

        post_login_result = await self.user_service.post_kakao_login(kakao_user_info)
        ticket = await self.ticket_service.issue_ticket(post_login_result.user_id,
                                                        ua_fingerprint=ua_fingerprint,
                                                        ttl_seconds=ticket_ttl_seconds)

        return KakaoAuthResult(
            user_id=post_login_result.user_id,
            raw_ticket=ticket,
            redirect_url=post_login_result.redirect_url,
        )
