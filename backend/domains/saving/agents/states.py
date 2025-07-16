from typing import Annotated, List, TypedDict

from domains.saving.schemas import SavingSearchResult


class SavingGraphState(TypedDict):
    user_query: str
    products: List[SavingSearchResult]
    explanation: str

    messages: Annotated[list, lambda x, y: x + y]

    search_offset: int
