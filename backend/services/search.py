import json
from db.repositories.deposit import DepositRepository
from db.repositories.faq import FaqRepository
from db.repositories.loan import LoanRepository
from schemas.embed import EmbedResult
from utils.embed import create_embedding_async


class AppSearchService:

    def __init__(
        self,
        faq_repo: FaqRepository,
        loan_repo: LoanRepository,
        deposit_repo: DepositRepository,
    ):
        self.faq_repo = faq_repo
        self.loan_repo = loan_repo
        self.deposit_repo = deposit_repo

    async def search_faqs(self, query: str, embeddings: EmbedResult):
        #embeddings = embed(query)

        faqs = self.faq_repo.search_hybrid(
            dense_vector=embeddings.dense,
            sparse_vector=embeddings.sparse,
        )

        faq_dicts = [
            {
                "title": faq.title,
                "content": faq.content,
                "url": faq.url,
                "category": faq.category.value, # type: ignore
            } for faq in faqs
        ]

        return json.dumps(faq_dicts, ensure_ascii=False)

    async def search_loans(self, query: str, embeddings: EmbedResult):
        #embeddings = embed(query)

        loan_chunks = self.loan_repo.search_hybrid(
            dense_vector=embeddings.dense,
            sparse_vector=embeddings.sparse,
        )

        loan_dicts = [
            {
                "title": chunk.loan.title,
                "description": chunk.loan.description,
                "url": chunk.loan.url,
                "content": chunk.content,
                "category": chunk.loan.category.value, # type: ignore
            } for chunk in loan_chunks
        ]

        return json.dumps(loan_dicts, ensure_ascii=False)

    async def search_deposits(self, query: str, embeddings: EmbedResult):
        #embeddings = embed(query)

        deposit_chunks = self.deposit_repo.search_hybrid(
            dense_vector=embeddings.dense,
            sparse_vector=embeddings.sparse,
        )

        deposit_dicts = [
            {
                "title": chunk.deposit.title,
                "url": chunk.deposit.url,
                "description": chunk.deposit.description,
                "content": chunk.content,
                "category": chunk.deposit.category.value, # type: ignore
            } for chunk in deposit_chunks
        ]

        return json.dumps(deposit_dicts, ensure_ascii=False)


def init_search_service():
    faq_repo = FaqRepository()
    loan_repo = LoanRepository()
    deposit_repo = DepositRepository()

    return AppSearchService(faq_repo, loan_repo, deposit_repo)
