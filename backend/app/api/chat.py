from fastapi import APIRouter
from openai import AsyncOpenAI

from schemas.chat import ChatRequest, ChatResponse

from dotenv import load_dotenv

from services.assistant import init_assistant

import json

load_dotenv()

router = APIRouter(prefix="/api")

client = AsyncOpenAI()

assistant = init_assistant()


@router.post("/chat", response_model=ChatResponse)
async def chat(req: ChatRequest):
    title = None
    if not req.messages:
        completion = await client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{
                "role":
                    "system",
                "content":
                    "당신은 사용자의 첫 질문을 바탕으로 채팅의 제목을 생성하는 assistant입니다. 10글자 내외의 짧은 제목을 작성하세요."
            }, {
                "role": "user",
                "content": req.question
            }])
        title = completion.choices[0].message.content

    history = [{
        "role":
            message.role,
        "content":
            json.dumps([content.model_dump_json() for content in message.content])
            if not isinstance(message.content, str) else message.content
    } for message in req.messages]

    answer = await assistant.pipeline_async(
        req.question,
        history=history,  #type: ignore
    )

    messages = [
        *req.messages, {
            "role": "user",
            "content": req.question,
        }, {
            "role": "assistant",
            "content": answer,
        }
    ]

    return {
        "title": title,
        "answer": answer,
        "question": req.question,
        "messages": messages,
    }
