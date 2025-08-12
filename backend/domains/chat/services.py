import asyncio
import json
from typing import AsyncGenerator, List, Optional

from fastapi.encoders import jsonable_encoder
from openai import AsyncOpenAI
from pymongo.results import UpdateResult
from app.core.config import AppConfig
from app.schemas.chat import ChatContentDTO, ChatResponseDTO
from domains.chat.models import Chat, ChatContent, ChatMessage
from domains.chat.repositories import ChatPreviewDTO, ChatRepository
from domains.user.repositories import UserRepository
from domains.user.services import UserNotFound

import os


class ChatNotFound(Exception):
    pass


UPSTAGE_API_KEY = os.getenv("UPSTAGE_API_KEY", "")


class ChatService:

    def __init__(self, *, cfg: AppConfig, user_repo: UserRepository,
                 chat_repo: ChatRepository):

        self.cfg = cfg.user
        self.user_repo = user_repo
        self.chat_repo = chat_repo

        self.openai_client = AsyncOpenAI(
            api_key=UPSTAGE_API_KEY,
            base_url="https://api.upstage.ai/v1",
        )

    async def generate_chat_title(self, chat_id: str, question: str) -> str:

        system_prompt = ("다음 사용자 질문에서 짧고 요약된 대화 제목을 한 문장으로 만들어주세요. "
                         "20자 이내로 간결하게 작성해주세요.")

        response = await self.openai_client.chat.completions.create(
            model="solar-pro",
            messages=[{
                "role": "system",
                "content": system_prompt
            }, {
                "role": "user",
                "content": question
            }],
            temperature=0.3,
            max_tokens=30,
        )

        title = response.choices[0].message.content or "새로운 대화"
        await self.chat_repo.upsert_chat(chat_id=chat_id, new_data={"title": title})

        return title

    async def create_chat(self, chat: Chat) -> Chat:
        if not await self.user_repo.get_user_by_id(chat.user_id):
            raise UserNotFound("User does not exist")

        return await self.chat_repo.insert_chat(chat)

    async def add_message(self, *, chat_id: str, message: ChatMessage) -> UpdateResult:
        if not await self.chat_repo.get_chat_by_chat_id(chat_id):
            raise ChatNotFound("Chat does not exist")

        return await self.chat_repo.add_message(chat_id, message)

    async def get_chat_list(self, *, user_id: str, size: int,
                            offset: int) -> List[ChatPreviewDTO]:

        if not await self.user_repo.get_user_by_id(user_id):
            raise UserNotFound("User does not exist")

        return await self.chat_repo.get_chats_by_user_id(user_id,
                                                         size=size,
                                                         offset=offset)

    async def get_chat_detail(self, chat_id: str):
        chat = await self.chat_repo.get_chat_by_chat_id(chat_id)
        if not chat:
            raise ChatNotFound("Chat does not exist")
        return chat

    async def chat_events(self, *, chat_id: Optional[str], user_id: str, message: str,
                          run_stream) -> AsyncGenerator[str, None]:

        if not chat_id:
            chat = await self.create_chat(Chat(user_id=user_id))
        else:
            chat = await self.get_chat_detail(chat_id)

        title_task = None
        if not chat.title:
            title_task = asyncio.create_task(self.generate_chat_title(chat.id, message))

        user_message = ChatMessage(role="user", content=ChatContent(message=message))
        print(chat.id)
        await self.add_message(chat_id=chat.id, message=user_message)

        products = []
        reply_chunks = []

        initial_response = ChatResponseDTO(
            chat_id=chat.id,
            status="pending",
            content=ChatContentDTO(message="질문을 이해하고 있습니다."))

        data_json = json.dumps(jsonable_encoder(initial_response), ensure_ascii=False)
        yield f"data: {data_json}\n\n"

        title_yielded = False

        async for _, chunk in run_stream(message, chat.id):
            payload = ChatResponseDTO(**chunk)
            data_json = json.dumps(jsonable_encoder(payload), ensure_ascii=False)

            yield f"data: {data_json}\n\n"

            match payload:
                case ChatResponseDTO(status="response",
                                     content=ChatContentDTO(products=None,
                                                            message=reply_chunk)):
                    reply_chunks.append(reply_chunk)

                case ChatResponseDTO(status="response",
                                     content=ChatContentDTO(products=_products)):
                    products = _products

            if not title_yielded and title_task and title_task.done():
                try:
                    title = title_task.result()
                except Exception:
                    title = "새로운 대화"

                _send_title = ChatResponseDTO(chat_id=chat.id,
                                              status="title",
                                              content=ChatContentDTO(message=title))
                yield f"data: {json.dumps(jsonable_encoder(_send_title), ensure_ascii=False)}\n\n"

                title_yielded = True

        assistant_message = ChatMessage(role="assistant",
                                        content=ChatContent(
                                            message="".join(reply_chunks),
                                            products=products))
        await self.add_message(chat_id=chat.id, message=assistant_message)

        yield "data: [DONE]\n\n"
