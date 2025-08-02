from datetime import datetime
from typing import List, Literal, Optional
import uuid
from pydantic import BaseModel, Field


class ChatProductOption(BaseModel):
    category: str
    value: str


class ChatProductPartialInfo(BaseModel):

    name: str

    product_type: Literal["saving", "deposit", "card", "insurance"]
    product_id: Optional[str] = None

    description: Optional[str] = None
    institution: str

    options: Optional[List[ChatProductOption]] = None
    tags: Optional[List[str]] = None
    details: Optional[str] = None


class ChatProductInfo(BaseModel):

    name: str

    product_type: Literal["saving", "deposit", "card", "insurance"]
    product_id: Optional[str] = None

    description: str
    institution: str

    options: List[ChatProductOption]
    tags: List[str] = []
    details: str


class ChatContent(BaseModel):

    message: Optional[str] = None
    products: Optional[List[ChatProductInfo]] = None


class ChatMessage(BaseModel):

    role: Literal["user", "assistant"]
    content: ChatContent


class Chat(BaseModel):

    id: str = Field(alias="_id",
                    default_factory=lambda _: str(uuid.uuid4()),
                    frozen=True)

    user_id: str

    title: Optional[str] = None
    messages: List[ChatMessage] = []

    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
