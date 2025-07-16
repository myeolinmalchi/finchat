from typing import AsyncGenerator, Iterable
from fastapi import APIRouter, HTTPException, Header
from starlette.responses import StreamingResponse

from app.crud import get_history, list_chats, save_msg, save_products, upsert_chat
from app.schemas.product import ProductInfoDTO, ProductOptionDTO
from app.schemas.chat import ChatContentDTO, ChatDetailResponse, ChatHistoryDTO, ChatListResponse, ChatPreviewDTO, ChatRequest, ChatResponseDTO, ChatResponseStatus

from fastapi.encoders import jsonable_encoder

from dotenv import load_dotenv

import json

import asyncio

load_dotenv()

router = APIRouter(prefix="")

DUMMY_PRODUCTS = [
    ProductInfoDTO(
        name="KB장병내일준비적금",
        product_type="saving",
        description="KB장병내일준비적금 (12개월, 최대 6.5%)",
        institution="KB국민은행",
        options=[ProductOptionDTO(category="가입기간", value="12개월")],
        tags=["군인혜택", "우대금리"],
        details="군 장병 전용 고금리 적금 상품",
    ),
    ProductInfoDTO(
        name="KB장병내일준비적금",
        product_type="saving",
        description="KB장병내일준비적금 (12개월, 최대 6.5%)",
        institution="KB국민은행",
        options=[ProductOptionDTO(category="가입기간", value="12개월")],
        tags=["군인혜택", "우대금리"],
        details="군 장병 전용 고금리 적금 상품",
    ),
    ProductInfoDTO(
        name="KB장병내일준비적금",
        product_type="saving",
        description="KB장병내일준비적금 (12개월, 최대 6.5%)",
        institution="KB국민은행",
        options=[ProductOptionDTO(category="가입기간", value="12개월")],
        tags=["군인혜택", "우대금리"],
        details="군 장병 전용 고금리 적금 상품",
    )
]

import re


def tokenize(
    text: str,
    tokens_per_chunk: int = 1,  # 1 = 한 단어씩
    max_chars_in_token: int | None = None  # 4~6으로 주면 긴 단어를 더 쪼갬
) -> Iterable[str]:
    """
    1) 공백 포함 단어 단위로 나눔
    2) tokens_per_chunk만큼 묶어서 yield
    3) 긴 단어(영어·URL 등)는 max_chars_in_token 길이로 추가 분할
    """
    words = re.findall(r"\S+\s*|\s+", text)  # '단어+공백' | '연속공백' 모두 보존
    for w in words:
        # (선택) 긴 단어 추가 세분화
        if max_chars_in_token and len(w.strip()) > max_chars_in_token:
            for i in range(0, len(w), max_chars_in_token):
                yield w[i:i + max_chars_in_token]
        else:
            yield w

    # tokens_per_chunk > 1 인 경우 다시 그룹핑
    if tokens_per_chunk > 1:
        buf, count = "", 0
        for token in tokenize(text, 1, max_chars_in_token):
            buf += token
            if token.strip():
                count += 1
            if count >= tokens_per_chunk:
                yield buf
                buf, count = "", 0
        if buf:
            yield buf


async def chat_events(req: ChatRequest) -> AsyncGenerator[str, None]:
    chat_id = upsert_chat(req.chat_id, None)
    user_content = ChatContentDTO(message=req.message)
    save_msg(chat_id, "user", jsonable_encoder(user_content))

    final_reply = ("여러 조건을 종합적으로 분석한 결과 "
                   "**KB장병내일준비적금**이 우대금리·가입편의성·군인전용 혜택 측면에서 "
                   "현재 가장 경쟁력이 높다고 판단했습니다.")
    assistant_content = ChatContentDTO(message=final_reply, products=DUMMY_PRODUCTS)


    steps: list[tuple[ChatResponseStatus, ChatContentDTO | None]] = [
        ("pending", ChatContentDTO(message="기준 금리를 확인하고 있습니다.")),
        ("pending", ChatContentDTO(message="보도 자료를 검색하고 있습니다.")),
        ("title", ChatContentDTO(message="군 장병 적금 상품 추천")),
        (
            "pending",
            ChatContentDTO(
                message="상품을 분석하고 있습니다.",
                products=[p.model_copy(deep=True) for p in DUMMY_PRODUCTS],
            ),
        ),
    ]

    steps.append(("response", ChatContentDTO(products=DUMMY_PRODUCTS)))

    for piece in tokenize(final_reply, tokens_per_chunk=2):
        steps.append(("response", ChatContentDTO(message=piece)))

    steps.append(("stop", None))

    for status, content in steps:
        payload = ChatResponseDTO(chat_id=chat_id, status=status, content=content)
        data_json = json.dumps(jsonable_encoder(payload), ensure_ascii=False)
        yield f"data: {data_json}\n\n"
        await asyncio.sleep(0.2)

    save_msg(chat_id, "assistant", jsonable_encoder(assistant_content))
    save_products(chat_id, jsonable_encoder(DUMMY_PRODUCTS))


    yield "data: [DONE]\n\n"


@router.post("", response_class=StreamingResponse)
async def stream_chat(
        body: ChatRequest,
        last_event_id: str | None = Header(None, convert_underscores=False),
):
    headers = {"Cache-Control": "no-cache"}
    return StreamingResponse(
        chat_events(body),
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
