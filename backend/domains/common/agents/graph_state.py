from operator import add
from typing import Annotated, Dict, List, Optional, TypedDict, Union

from langchain_core.language_models import BaseChatModel
from langchain_core.messages import BaseMessage
from langgraph.graph.message import add_messages

from domains.saving.schemas import SavingSearchResult

ProductSearchResults = Union[List[SavingSearchResult]] | None
ProductSearchResult = Union[SavingSearchResult]


class _Tool(TypedDict):

    tool_name: str
    tool_args: Dict


class GraphState(TypedDict):

    messages: Annotated[list[BaseMessage], add_messages]
    chat_id: str
    tavily_results: Optional[dict]

    tool: Optional[_Tool]

    candidates: ProductSearchResults  # 추천 상품 후보
    selected: Annotated[ProductSearchResults, add]  # 실제 선택된 상품

    offset: int
    target_count: int  # 목표 상품 개수

    next: Optional[str]
