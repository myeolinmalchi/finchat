from dataclasses import dataclass
from typing import Tuple
from app.core.config import AppConfig
from app.schemas.user import UserIn
from domains.auth.services import KakaoUserInfoResponse
from domains.user.models import SocialAccount, User
from domains.user.repositories import UserRepository, SocialRepository


@dataclass(frozen=True)
class PostLoginResult:
    redirect_url: str
    user_id: str
    created_temp: bool


class UserNotFound(Exception):
    pass


class SocialAccountNotFound(Exception):
    pass


class AlreadyRegistered(Exception):
    pass


class UserService:

    def __init__(self, *, cfg: AppConfig, user_repo: UserRepository,
                 social_repo: SocialRepository):

        self.cfg = cfg.user
        self.user_repo = user_repo
        self.social_repo = social_repo

    async def post_kakao_login(
            self, kakao_user_info: KakaoUserInfoResponse) -> PostLoginResult:

        kakao_user_id: str = str(kakao_user_info.kakao_user_id)
        social_account = await self.social_repo.get_by_provider_id(
            "kakao", kakao_user_id)

        match social_account:

            case SocialAccount(temp=True):
                # 소셜 계정이 존재하지만 임시 계정인 경우
                return PostLoginResult(
                    redirect_url=self.cfg.signup_redirect_url,
                    user_id=social_account.user_id,
                    created_temp=True,
                )

            case SocialAccount(temp=False):
                # 가입된 소셜 계정이 존재하는 경우
                return PostLoginResult(
                    redirect_url=self.cfg.client_origin,
                    user_id=social_account.user_id,
                    created_temp=False,
                )

            case _:
                # 소셜 계정이 존재하지 않는 경우
                new_user = await self.user_repo.create_user(
                    User(
                        email=kakao_user_info.email,
                        nickname=kakao_user_info.nickname,
                        profile_image_url=kakao_user_info.profile_image_url,
                    ))

                await self.social_repo.create(
                    SocialAccount(user_id=new_user.id,
                                  provider="kakao",
                                  provider_user_id=str(kakao_user_id)))

                return PostLoginResult(
                    redirect_url=self.cfg.signup_redirect_url,
                    user_id=new_user.id,
                    created_temp=True,
                )

    async def signup(self, user_id: str, user_in: UserIn):

        social_account = await self.social_repo.get_by_user_id(user_id)

        match social_account:
            case None:
                raise SocialAccountNotFound()
            case SocialAccount(temp=False):
                raise AlreadyRegistered()

        await self.social_repo.update(user_id=user_id, update_data={"temp": False})
        user = await self.user_repo.update_user(user_id, user_in.model_dump())

        return user

    async def get_user_by_id(self, user_id: str) -> Tuple[User, SocialAccount]:
        user = await self.user_repo.get_user_by_id(user_id)
        if not user:
            raise UserNotFound(f"유효하지 않은 사용자입니다. ({user_id})")
        user_social = await self.social_repo.get_by_user_id(user_id)
        if not user_social:
            raise SocialAccountNotFound(f"유효하지 않은 사용자입니다. ({user_id})")
        return user, user_social
