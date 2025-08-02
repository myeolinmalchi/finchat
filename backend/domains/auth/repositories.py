from typing import Dict, Optional, Any
from motor.motor_asyncio import AsyncIOMotorDatabase
from pymongo.results import DeleteResult, UpdateResult

from app.core.config import AppConfig
from domains.user.models import Token


class TicketRepository:

    def __init__(self, *, cfg: AppConfig, db: AsyncIOMotorDatabase):
        self.col = db.get_collection(cfg.mongo.collections.tickets)

    async def ensure_indexes(self) -> None:
        await self.col.create_index([("ticket_hash", 1)], unique=True, background=True)
        await self.col.create_index([("expires_at", 1)],
                                    expireAfterSeconds=0,
                                    background=True)

    async def insert(self, doc: dict) -> None:
        await self.col.insert_one(doc)

    async def find_one_and_delete(self, *, ticket_hash: str,
                                  ua_fingerprint: Optional[str]) -> Optional[dict]:
        query = {"ticket_hash": ticket_hash}
        if ua_fingerprint is not None:
            query["ua_fingerprint"] = ua_fingerprint
        return await self.col.find_one_and_delete(query)


class TokenRepository:

    def __init__(self, *, cfg: AppConfig, db: AsyncIOMotorDatabase):
        self.col = db.get_collection(cfg.mongo.collections.tokens)

    async def upsert_tokens(self, user_id: str, refresh_token: str,
                            new_data: Dict[str, Any]) -> UpdateResult:
        return await self.col.update_one(
            {
                "user_id": user_id,
                "refresh_token": refresh_token
            }, {"$set": new_data},
            upsert=True)

    async def insert_token(self, token: Token) -> Token:
        await self.col.insert_one(token.model_dump(by_alias=True))
        return token

    async def get_tokens_by_refresh_token(self, refresh_token: str) -> Optional[Token]:
        raw = await self.col.find_one({"refresh_token": refresh_token})
        return Token.model_validate(raw) if raw else None

    async def get_tokens_by_user_and_refresh_token(
            self, user_id: str, refresh_token: str) -> Optional[Token]:
        raw = await self.col.find_one({
            "refresh_token": refresh_token,
            "user_id": user_id
        })
        return Token.model_validate(raw) if raw else None

    async def delete_tokens(self,
                            *,
                            user_id: Optional[str] = None,
                            refresh_token: Optional[str] = None) -> int:

        query: Dict[str, Any] = {}
        if user_id:
            query["user_id"] = user_id
        if refresh_token:
            query["refresh_token"] = refresh_token

        result: DeleteResult = await self.col.delete_many(query)
        return result.deleted_count
