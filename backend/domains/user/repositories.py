from datetime import datetime
from typing import Optional, Dict, Any

from motor.motor_asyncio import AsyncIOMotorDatabase
from pymongo.results import DeleteResult

from app.core.config import AppConfig
from domains.user.models import SocialProviders, SocialAccount, User


class SocialRepository:

    def __init__(self, *, cfg: AppConfig, db: AsyncIOMotorDatabase):
        self.collection = db.get_collection(cfg.mongo.collections.social_accounts)

    async def get_by_provider_id(self, provider: SocialProviders,
                                 provider_user_id: str):
        social_raw = await self.collection.find_one({
            "provider_user_id": str(provider_user_id),
            "provider": provider
        })

        return SocialAccount.model_validate(social_raw) if social_raw else None

    async def get_by_user_id(self, user_id: str):
        social_raw = await self.collection.find_one({
            "user_id": user_id,
        })

        return SocialAccount.model_validate(social_raw) if social_raw else None

    async def update(self, user_id: str,
                     update_data: Dict[str, Any]) -> Optional[SocialAccount]:
        update_payload = {k: v for k, v in update_data.items() if v is not None}
        if not update_payload:
            return await self.get_by_user_id(user_id)

        update_payload["updated_at"] = datetime.utcnow()
        user_raw = await self.collection.find_one_and_update({"_id": user_id},
                                                             {"$set": update_payload},
                                                             return_document=True)

        return SocialAccount.model_validate(user_raw)

    async def create(self, social: SocialAccount) -> SocialAccount:
        await self.collection.insert_one(social.model_dump(by_alias=True))
        return social


class UserRepository:

    def __init__(self, *, cfg: AppConfig, db: AsyncIOMotorDatabase):
        self.collection = db.get_collection(cfg.mongo.collections.users)

    async def create_user(self, user: User) -> User:
        await self.collection.insert_one(user.model_dump(by_alias=True))
        return user

    async def get_user_by_id(self, user_id: str) -> Optional[User]:
        user_raw = await self.collection.find_one({"_id": user_id})
        return User.model_validate(user_raw) if user_raw else None

    async def get_user_by_email(self, email: str) -> Optional[User]:
        user_raw = await self.collection.find_one({"email": email})
        return User.model_validate(user_raw) if user_raw else None

    async def update_user(self, user_id: str, update_data: Dict[str,
                                                                Any]) -> Optional[User]:
        """기존 유저 정보 수정"""
        update_payload = {k: v for k, v in update_data.items() if v is not None}

        if not update_payload:
            return await self.get_user_by_id(user_id)

        update_payload["updated_at"] = datetime.utcnow()

        user_raw = await self.collection.find_one_and_update({"_id": user_id},
                                                             {"$set": update_payload},
                                                             return_document=True)

        return User.model_validate(user_raw)

    async def delete_user(self, user_id: str) -> bool:
        """유저 삭제"""

        result: DeleteResult = await self.collection.delete_one({"_id": user_id})
        return result.deleted_count > 0
