from db.models.deposit import DepositModel, DepositChunkModel
from .base import BaseRepository

from sqlalchemy import func, select

from typing import Any, Dict, List, Optional

from pgvector import SparseVector
from db.common import V_DIM


class DepositRepository(BaseRepository[DepositModel]):

    async def search_hybrid(
        self,
        dense_vector: Optional[List[float]] = None,
        sparse_vector: Optional[Dict[Any, float]] = None,
        lexical_ratio: float = 0.5,
        k: int = 5,
    ):
        """내용으로 유사도 검색"""

        score_dense_content = 1 - DepositChunkModel.dense_vector.cosine_distance(dense_vector)
        score_lexical_content = -1 * (
            DepositChunkModel.sparse_vector.max_inner_product(SparseVector(sparse_vector, V_DIM))
        )

        score_content = ((score_lexical_content * lexical_ratio) + score_dense_content *
                         (1 - lexical_ratio)).label("score_content")

        stmt = select(DepositChunkModel).order_by(score_content.desc()).limit(k)
        result = await self.session.execute(stmt)
        return result.scalars().all()
