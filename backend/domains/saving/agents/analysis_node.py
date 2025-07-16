import asyncio
from langchain_core.language_models import BaseChatModel
from langchain_core.messages import ToolMessage

import re

from domains.saving.agents.states import SavingGraphState
from domains.saving.schemas import TotalSavingSearchResult

SAVING_ANALYSIS_PROMPT = """\
당신은 적금 상품이 질문 상황에 적합한지 분석하는 에이전트다.
주어진 적금 상품의 가입 조건, 대상, 우대금리 등에 대한 정보를 면밀히 분석하여
질문 내용과 맥락에 부합하는 상품인지 분석하여라.

응답은 반드시 Yes 또는 No로 시작해야 한다.
Yes: 부합하는 상품, No: 부합하지 않는 상품

질문: {}"""


def init_saving_analysis_node(
    llm: BaseChatModel,
    system_prompt: str = SAVING_ANALYSIS_PROMPT,
):

    async def node(state: SavingGraphState):

        tool_call_message = state["messages"][-1]

        if not isinstance(tool_call_message, ToolMessage):
            return {"products": []}

        raw_search_result = tool_call_message.content
        search_result = TotalSavingSearchResult.model_validate(raw_search_result)
        savings = search_result.savings

        ainvoke_coroutines = [
            llm.ainvoke([
                ("system", system_prompt.format(state["user_query"])),
                ("user", saving.model_dump_json()),
            ]) for saving in savings
        ]

        responses = await asyncio.gather(*ainvoke_coroutines)

        cleaned_responses = [
            re.sub(r"<think>.*?</think>", "", str(response.content), flags=re.DOTALL)
            for response in responses
        ]
        selected = [
            saving for saving, response in zip(savings, cleaned_responses)
            if "Yes" in response
        ]

        return {"products": selected}

    return node
