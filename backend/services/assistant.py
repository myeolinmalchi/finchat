from abc import abstractmethod
import inspect
import json
from typing import Generic, List, Optional, TypeVar

from aiohttp import ClientSession
from openai import AsyncClient
from openai.types.chat import ChatCompletionMessageParam
from agents import kb0
from agents.schemas import KB0_Answer
from services.search import AppSearchService, init_search_service
from utils.embed import create_embedding_async
from itertools import chain

import asyncio

from common.http import HTTPMetaclass

AssistantAnswerT = TypeVar("AssistantAnswerT")


class IAssistantService(Generic[AssistantAnswerT], metaclass=HTTPMetaclass):

    def __init__(
        self,
        kb0: kb0.KB0,
        kb0_1: kb0.KB0_1,
        kb0_2: kb0.KB0_2,
        kb0_4: kb0.KB0_4,
        search_service: AppSearchService,
    ):
        self.kb0 = kb0
        self.kb0_1 = kb0_1
        self.kb0_2 = kb0_2
        self.kb0_4 = kb0_4
        self.search_service = search_service

    async def call_by_name(self, tool_name: str, **args) -> List[str]:
        func = getattr(self.search_service, tool_name)
        if inspect.iscoroutinefunction(func):
            return await func(**args)
        return func(**args)

    async def pipeline_async(
        self,
        question: str,
        history: List[ChatCompletionMessageParam],
        session: Optional[ClientSession] = None,
    ):
        if not session:
            raise ValueError

        return await self._pipeline_async(question, history, session)

    @abstractmethod
    async def _pipeline_async(
        self,
        question: str,
        history: List[ChatCompletionMessageParam],
        session: ClientSession,
    ) -> AssistantAnswerT:
        pass


class AssistantService(IAssistantService[str]):

    def __init__(
        self,
        kb0: kb0.KB0,
        kb0_1: kb0.KB0_1,
        kb0_2: kb0.KB0_2,
        kb0_4: kb0.KB0_4,
        search_service: AppSearchService,
    ):
        self.kb0 = kb0
        self.kb0_1 = kb0_1
        self.kb0_2 = kb0_2
        self.kb0_4 = kb0_4
        self.search_service = search_service

    async def _pipeline_async(self, question, history, session):

        print("before extract sub questions...")
        kb0_1_response = await self.kb0_1.inference(question, history)

        if not kb0_1_response:
            raise ValueError

        sub_questions = kb0_1_response.sub_questions

        print("embed sub questions...")
        sub_question_embeddings = await create_embedding_async(
            sub_questions,
            session=session,
            chunking=False,
            html=False,
        )
        print(sub_questions)

        print("choose search tools...")
        kb0_2_futures = [self.kb0_2.inference(q, history) for q in sub_questions]
        kb0_2_responses = await asyncio.gather(*kb0_2_futures)
        tools = [res.tools for res in kb0_2_responses if res is not None]
        print(tools)

        print("run tools...")
        tool_result_futures = [
            asyncio.gather(
                *[self.call_by_name(tool_name=_tool.value, **{
                    "query": q,
                    "embeddings": es,
                }) for _tool in tool]
            ) for tool, q, es in zip(tools, sub_questions, sub_question_embeddings)
        ]

        tool_results = await asyncio.gather(*tool_result_futures)

        print("extract essential infos...")

        kb0_4_futures = [
            self.kb0_4.inference(q, history, context="\n".join(_tool_result))
            for q, tool_result in zip(sub_questions, tool_results) for _tool_result in tool_result
        ]

        kb0_4_responses = await asyncio.gather(*kb0_4_futures)
        documents = [res.documents for res in kb0_4_responses if res is not None]

        if not documents:
            raise ValueError

        flattened_documents = list(chain(*documents))
        flattened_documents = [doc.model_dump() for doc in flattened_documents]

        document_strs = json.dumps(flattened_documents, ensure_ascii=False)

        print("create final answer...")
        kb0_response = await self.kb0.inference(question, history, context=document_strs)

        if not kb0_response:
            raise ValueError

        url2md = lambda url: f"[FILE]({url})" if "download" in url else f"[URL]({url})"
        final_answer = "\n\n".join([
            answer.paragraph + " " + "".join(map(url2md, answer.urls)) for answer in kb0_response.answers
        ])

        return final_answer


class AssistantServiceV2(IAssistantService[List[KB0_Answer]]):

    async def _pipeline_async(self, question, history, session):

        print("before extract sub questions...")
        kb0_1_response = await self.kb0_1.inference(question, history)

        if not kb0_1_response:
            raise ValueError

        sub_questions = kb0_1_response.sub_questions

        print("embed sub questions...")
        sub_question_embeddings = await create_embedding_async(
            sub_questions,
            session=session,
            chunking=False,
            html=False,
        )
        print(sub_questions)

        print("choose search tools...")
        kb0_2_futures = [self.kb0_2.inference(q, history) for q in sub_questions]
        kb0_2_responses = await asyncio.gather(*kb0_2_futures)
        tools = [res.tools for res in kb0_2_responses if res is not None]
        print(tools)

        print("run tools...")
        tool_result_futures = [
            asyncio.gather(
                *[self.call_by_name(tool_name=_tool.value, **{
                    "query": q,
                    "embeddings": es,
                }) for _tool in tool]
            ) for tool, q, es in zip(tools, sub_questions, sub_question_embeddings)
        ]

        tool_results = await asyncio.gather(*tool_result_futures)

        print("extract essential infos...")

        kb0_4_futures = [
            self.kb0_4.inference(q, history, context="\n".join(_tool_result))
            for q, tool_result in zip(sub_questions, tool_results) for _tool_result in tool_result
        ]

        kb0_4_responses = await asyncio.gather(*kb0_4_futures)
        documents = [res.documents for res in kb0_4_responses if res is not None]

        if not documents:
            raise ValueError

        flattened_documents = list(chain(*documents))
        flattened_documents = [doc.model_dump() for doc in flattened_documents]

        document_strs = json.dumps(flattened_documents, ensure_ascii=False)

        print("create final answer...")
        kb0_response = await self.kb0.inference(question, history, context=document_strs)

        if not kb0_response:
            raise ValueError

        return kb0_response.answers


def init_assistant() -> IAssistantService:
    search_service = init_search_service()

    client = AsyncClient()
    model = "gpt-4o-mini"
    temperature = 0.3

    kb0_1 = kb0.KB0_1(client, model, temperature)
    kb0_2 = kb0.KB0_2(client, model, temperature)
    kb0_4 = kb0.KB0_4(client, model, temperature)
    kb0_ = kb0.KB0(client, model, temperature)

    return AssistantServiceV2(kb0_, kb0_1, kb0_2, kb0_4, search_service)
