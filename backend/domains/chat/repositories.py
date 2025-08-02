from dataclasses import dataclass
from datetime import datetime
from typing import List
from motor.motor_asyncio import AsyncIOMotorDatabase
from pymongo.results import UpdateResult
from app.core.config import AppConfig
from domains.chat.models import Chat, ChatMessage


@dataclass
class ChatPreviewDTO:

    chat_id: str
    title: str

    created_at: datetime
    updated_at: datetime


class ChatRepository:

    def __init__(self, *, cfg: AppConfig, db: AsyncIOMotorDatabase):
        self.col = db.get_collection(cfg.mongo.collections.chats)

    async def add_message(self, chat_id: str, message: ChatMessage) -> UpdateResult:
        return await self.col.update_one({
            "_id": chat_id,
        }, {"$push": {
            "messages": message.model_dump(by_alias=True)
        }})

    async def insert_chat(self, chat: Chat):
        await self.col.insert_one(chat.model_dump(by_alias=True))
        return chat

    async def upsert_chat(self, chat_id: str, new_data: dict):
        return await self.col.update_one(
            {"_id": chat_id},
            {"$set": new_data},
            upsert=True,
        )

    async def get_chats_by_user_id(self,
                                   user_id: str,
                                   *,
                                   size: int = 20,
                                   offset: int = 0) -> List[ChatPreviewDTO]:
        cursor = self.col.find({"user_id": user_id}).skip(offset).limit(size)
        raw_chats = await cursor.to_list(length=size)

        chat_previews = [
            ChatPreviewDTO(
                chat_id=chat["_id"],
                title=chat["title"],
                created_at=chat["created_at"],
                updated_at=chat["updated_at"],
            ) for chat in raw_chats
        ]

        return chat_previews

    async def get_chat_by_chat_id(self, chat_id: str):

        raw = await self.col.find_one({"_id": chat_id})
        return Chat.model_validate(raw) if raw else None
