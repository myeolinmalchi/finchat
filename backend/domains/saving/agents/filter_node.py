from typing import List, Dict
from langchain_core.language_models import BaseChatModel
from langchain_core.tools import BaseTool
from langgraph.config import get_stream_writer

from domains.saving.agents.graph_state import SavingGraphState


def init_filter_node(llm: BaseChatModel):

    async def node(state: SavingGraphState):
        writer = get_stream_writer()

        # TODO: LLM 기반 필터링 추가
        filtered = state.get("candidates", [])
        state["selected"] = state.get("selected", []) + filtered

        state["candidates"] = []

        # TODO: 스트림 출력 구현
        writer({
            "chat_id": state["chat_id"],
            "status": "pending",
            "content": {
                "message": "상품을 분석하고 있습니다.",
                "products": filtered
            }
        })
        state["next"] = "router"

        return state

    return node
