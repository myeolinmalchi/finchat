import re
from langchain_core.language_models import BaseChatModel
from langchain_core.prompts import ChatPromptTemplate
from langgraph.config import get_stream_writer

from langchain_upstage import ChatUpstage

from domains.common.agents.graph_state import (
    GraphState,
    ProductSearchResult,
)
from domains.saving.agents.prompts import (SAVING_ANALYSIS_SYSTEM_PROMPT,
                                           SAVING_ANALYSIS_USER_PROMPT_TEMPLATE)

import asyncio


async def _evaluate_product_fit(
    llm: BaseChatModel,
    product: ProductSearchResult,
    state: GraphState,
) -> bool:

    prompt_template = ChatPromptTemplate([
        ("system", SAVING_ANALYSIS_SYSTEM_PROMPT),
        ("user", SAVING_ANALYSIS_USER_PROMPT_TEMPLATE),
    ])

    prompt = prompt_template.invoke({
        "user_info": "",
        "user_question": str(state["messages"][0].content),
        "product_info": str(product)
    })

    res = await llm.ainvoke(prompt)
    result = str(res.content)

    match llm:
        case ChatUpstage(model="solar-pro2"):
            result = re.sub(r'<think>.*?</think>', '', result, flags=re.DOTALL)

    if result == "부적합":
        return False
    if result == "적함":
        return True
    if "부적합" in result:
        return False
    return True


def init_filter_node(llm: BaseChatModel):

    async def node(state: GraphState):
        print("============ Fileter Node ============")
        writer = get_stream_writer()

        products = state.get("candidates") or []

        writer({
            "chat_id": state["chat_id"],
            "status": "pending",
            "content": {
                "message":
                    "상품을 분석하고 있습니다.",
                "products": [{
                    "name": p.product.name,
                    "product_type": "saving",
                    "institution": p.product.institution
                } for p in products]
            }
        })

        eval_result = await asyncio.gather(
            *[_evaluate_product_fit(llm, product, state) for product in products])
        filtered = [product for eval, product in zip(eval_result, products) if eval]

        return {
            "selected": filtered,
            "next": "router",
        }

    return node
