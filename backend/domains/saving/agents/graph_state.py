from typing import Dict, List, Optional, TypedDict

from langchain_core.messages import BaseMessage

from domains.saving.schemas import SavingSearchResult


class _Tool(TypedDict):

    tool_name: str
    tool_args: Dict


class SavingGraphState(TypedDict):
    """적금 그래프 전반에서 공유되는 상태"""

    chat_id: str
    messages: List[BaseMessage]
    tavily_results: Optional[dict]

    tool: Optional[_Tool]

    candidates: Optional[List[SavingSearchResult]]  # 추천 후보
    selected: Optional[List[SavingSearchResult]]  # 실제 선택된 추천 상품

    offset: int  # 검색 offset
    target_count: int

    next: Optional[str]
