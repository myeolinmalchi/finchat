from fastapi import APIRouter, Depends, Header, Request, status
from fastapi.responses import JSONResponse
from starlette.responses import StreamingResponse

from app.core.deps import inject
from app.dependencies import get_workflow_stream
from app.schemas.chat import (ChatDetailResponse, ChatListResponse, ChatRequest)

from dotenv import load_dotenv

from domains.chat.services import ChatService

load_dotenv()

router = APIRouter(prefix="")


@router.post("", response_class=StreamingResponse)
async def stream_chat(
        body: ChatRequest,
        last_event_id: str | None = Header(None, convert_underscores=False),
        run_stream=Depends(get_workflow_stream),
):
    headers = {"Cache-Control": "no-cache"}

    return StreamingResponse(
        chat_events(body, run_stream),
        media_type="text/event-stream",
        headers=headers,
    )


@router.get("", response_model=ChatListResponse)
async def get_chat_list(offset: int = 0, size: int = 20):
    rows = list_chats(offset, size)
    return ChatListResponse(size=len(rows),
                            offset=offset,
                            items=[ChatPreviewDTO(**r) for r in rows])


@router.get("/{chat_id}", response_model=ChatDetailResponse)
async def get_chat_detail(chat_id: str, offset: int = 0, size: int = 20):
    rows = get_history(chat_id, offset, size)
    if not rows:
        raise HTTPException(status_code=404, detail="chat not found")
    items = [
        ChatHistoryDTO(role=r["role"], content=json.loads(r["content"])) for r in rows
    ]
    return ChatDetailResponse(size=len(items), offset=offset, items=items)
