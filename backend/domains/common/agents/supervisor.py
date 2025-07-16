import asyncio
from pprint import pprint
from typing import AsyncIterator, Literal, TypedDict
from langchain_core.language_models import BaseChatModel
from langchain_core.messages import HumanMessage
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai.chat_models.base import ChatOpenAI
from langchain_upstage import ChatUpstage
from langgraph.graph import END, StateGraph
from motor.motor_asyncio import AsyncIOMotorDatabase
from common.database import init_mongodb_client
from domains.common.agents.graph_state import GraphState
from domains.common.agents.research_node import init_research_node
from domains.saving.agents.explain_node import init_explain_node
from domains.saving.agents.saving_subgraph import init_saving_subgraph
from domains.saving.agents.tool_factory import init_saving_retrieval_tools

Members = Literal["explain_node", "saving_node", "research_node"]
Options = Literal[Members, "END"]

system_prompt = (
    "You are a supervisor agent managing the following workers: "
    f"{Members.__args__}. The user's main goal is to receive financial product recommendations "
    "that fit their needs, regardless of the type of question they ask.\n\n"
    "- 'saving_node': 사용자의 현재 상황과 요청 내용을 바탕으로 적합한 적금 상품을 검색하는 노드입니다.\n"
    "- 'explain_node': 추천 상품 목록에 데이터가 존재하면 검색 결과에 대한 설명을 작성하고 워크플로우를 종료합니다.\n"
    "- 'research_node': 금융 지식, 뉴스 기사, 정부 정책 등의 외부 지식을 보충하기 위해 사용합니다. **정보 검색을 위한 보조 수단으로만 사용합니다.**\n\n"
)


class Router(TypedDict):
    next: Members


def init_supervisor_node(llm: BaseChatModel):

    async def supervisor_node(state: GraphState):
        print("============ Supervisor Node ============")

        products = state["selected"]

        if products and len(products) >= state["target_count"]:
            return {"next": "explain_node"}

        products_str = "### 추천 상품 목록:"
        if products:
            products_str += "\n".join([
                f"{idx}. {product.product.name}"
                for idx, product in enumerate(products, 1)
            ])
        else:
            products_str += " 없음"

        messages = [
            {
                "role": "system",
                "content": system_prompt + products_str
            },
        ] + state["messages"]

        res = await llm.with_structured_output(Router).ainvoke(messages)
        next_ = res["next"]  # type: ignore

        return {"next": next_}

    return supervisor_node


def init_graph(
    llm: BaseChatModel,
    db: AsyncIOMotorDatabase,
    target_count: int = 3,
):
    sg = StateGraph(GraphState)

    llm_with_reasoning = ChatUpstage(
        model="solar-pro2",
        temperature=0.0,
        reasoning_effort="high",
        max_tokens=16384,
    )

    saving_tools = init_saving_retrieval_tools(db.get_collection("savings"))
    sg.add_node("saving_node", init_saving_subgraph(llm, saving_tools))

    sg.add_node("research_node", init_research_node(llm))
    sg.add_node("explain_node", init_explain_node(llm))
    sg.add_node("supervisor", init_supervisor_node(llm_with_reasoning))

    sg.add_edge("research_node", "supervisor")
    sg.add_edge("saving_node", "supervisor")
    sg.add_edge("explain_node", END)

    sg.add_conditional_edges("supervisor", lambda s: s["next"])

    sg.set_entry_point("supervisor")

    graph = sg.compile()

    async def stream_graph(user_msg: str, chat_id: str) -> AsyncIterator[dict]:
        init_state: GraphState = {
            "chat_id": chat_id,
            "messages": [HumanMessage(content=user_msg)],
            "tavily_results": None,
            "candidates": [],
            "selected": [],
            "offset": 0,
            "target_count": target_count,
            "tool": None,
            "next": None,
        }
        async for chunk in graph.astream(init_state,
                                         stream_mode="custom",
                                         subgraphs=True,
                                         config={"recursion_limit": 100}):
            yield chunk

    return stream_graph


import asyncio


async def run(query: str):
    """
    llm = ChatOpenAI(
        model="gpt-4o-mini",
        temperature=0.3,
    )
    """
    llm = ChatUpstage(
        model="solar-pro2",
        temperature=0.0,
        reasoning_effort="low",
        max_tokens=16384,
    )

    _, db = init_mongodb_client()
    run = init_graph(llm, db)

    async for _, chunk in run(query, ""):
        if chunk["status"] == "response":
            print(chunk["content"]["message"], end="")
        else:
            print(chunk)


if __name__ == "__main__":
    asyncio.run(run("월 50씩 1년동안 모으려고 하는데 괜찮은 적금 추천좀 해주세요"))
