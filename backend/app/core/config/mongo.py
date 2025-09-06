from dataclasses import dataclass, field

import os
from typing import Optional

from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase


@dataclass(frozen=True)
class MongoCollections:

    users: str = field(default_factory=lambda: os.getenv("COL_USERS", "users"))
    user_memories: str = field(
        default_factory=lambda: os.getenv("COL_USER_MEMORIES", "user_memories"))
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
