from datetime import datetime
from typing import Any, Dict, Literal, Optional

from pydantic import BaseModel, Field

import uuid

SocialProviders = Literal["kakao", "google"]


class User(BaseModel):
    """유저 정보 스키마"""

    id: str = Field(alias="_id",
                    default_factory=lambda _: str(uuid.uuid4()),
                    frozen=True)

    email: Optional[str] = None
    nickname: Optional[str] = None

    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    profile_image_url: Optional[str] = None

    #model_config = ConfigDict(populate_by_name=True)


class SocialAccount(BaseModel):
    """소셜 로그인 정보 스키마"""

    id: str = Field(alias="_id",
                    default_factory=lambda _: str(uuid.uuid4()),
                    frozen=True)

    user_id: str

    provider: SocialProviders
    provider_user_id: str

    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    temp: bool = True  # 임시 계정 여부

    #model_config = ConfigDict(populate_by_name=True)


class Token(BaseModel):
    """유저 인증 토큰 관리를 위한 데이터 스키마"""

    id: str = Field(default_factory=lambda: str(uuid.uuid4()), alias="_id")
    user_id: str
    access_token: str
    refresh_token: str
    access_token_expires_at: datetime
    refresh_token_expires_at: datetime

    #model_config = ConfigDict(populate_by_name=True)


class UserMemory(BaseModel):
    """사용자 장기 메모리 도큐먼트 스키마"""

    id: str = Field(default_factory=lambda: str(uuid.uuid4()), alias="_id")

    user_id: str
    content: str
    category: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)

    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
