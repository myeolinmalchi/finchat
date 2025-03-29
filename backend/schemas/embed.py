from typing import Dict, List, Optional
from pydantic import BaseModel


class EmbedResult(BaseModel):
    chunk: Optional[str]
    dense: List[float]
    sparse: Dict[str, float]


class RerankResult(BaseModel):
    index: int
    score: float
