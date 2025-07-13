import asyncio
from typing import List, Literal
from langchain_core.language_models import BaseChatModel
from langchain_core.messages import HumanMessage
from langgraph.prebuilt import create_react_agent
from motor.motor_asyncio import AsyncIOMotorDatabase
from pydantic import BaseModel
from typing_extensions import TypedDict

from langchain_openai import ChatOpenAI

from common.database import init_mongodb_client
from domains.common.agents.states import AgentState

from langgraph.graph import StateGraph, START, END

from domains.saving.agents.agent_factory import init_saving_search_node
from domains.saving.agents.tool_factory import init_saving_retrieval_tools

members = ["saving_node", "search"]
options = members + ["FINISH"]

system_prompt = (
    "You are a supervisor agent managing the following workers: "
    f"{members}. The user's main goal is to receive financial product recommendations "
    "that fit their needs, regardless of the type of question they ask.\n\n"
    "- 'saving_node': Searches internal saving products and recommends suitable options based on the user's situation and goals.\n"
    "- 'search': Uses external web search to collect additional context or details that can improve the financial product recommendation.\n\n"
    "For every user request, you must always:\n"
    "1. You MUST PROVIDE relevant financial product recommendations.\n"
    "2. Answer the user's original question directly, whether it's about calculations, explanations, or external information.\n\n"
    "Decide which worker should act next based on the user's message and previous results. "
    "If no further action is needed, return FINISH.")


class Router(TypedDict):
    """Worker to route to next. If no workers needed, route to FINISH."""

    next: Literal["saving_node", "search", "explain_node", "FINISH"]


from langchain_tavily import TavilySearch

search_tool = TavilySearch(max_results=5, include_answer=True, include_raw_content=True)


def init_tavily_node(llm: BaseChatModel):

    agent = create_react_agent(
        model=llm,
        tools=[search_tool],
    )

    async def node(state: AgentState):
        result = await agent.ainvoke(state)

        return {
            "messages": [
                HumanMessage(content=result["messages"][-1].content,
                             name="saving_agent")
            ],
            "next": "supervisor"
        }

    return node


class SavingProduct(BaseModel):
    name: str
    institution: str
    base_rate: float
    max_rate: float
    pros: List[str]
    cons: List[str]
    features: List[str]
    recommended_reason: str


class SavingRecommendation(BaseModel):

    products: List[SavingProduct]
    explain: str


def init_explain_node(llm: BaseChatModel):

    structured = llm.with_structured_output(SavingRecommendation)

    async def node(state: AgentState):
        result = await structured.ainvoke(state["messages"][-1].content)

        return {
            "messages": [HumanMessage(content=str(result), name="explain_agent")],
            "next": "supervisor"
        }

    return node


def init_supervisor_node(llm: BaseChatModel):

    async def supervisor_node(state: AgentState) -> AgentState:
        messages = [
            {
                "role": "system",
                "content": system_prompt
            },
        ] + state["messages"]

        response = await llm.with_structured_output(Router).ainvoke(messages)
        next_ = response["next"]  # type: ignore
        if next_ == "FINISH":
            next_ = END

        return {"next": next_, "messages": []}

    return supervisor_node


def build_graph(db: AsyncIOMotorDatabase):

    llm = ChatOpenAI(model="gpt-4o", temperature=0.3)

    supervisor_node = init_supervisor_node(llm)

    saving_tools = init_saving_retrieval_tools(db.get_collection("savings"))
    saving_node = init_saving_search_node(llm, saving_tools)

    tavily_node = init_tavily_node(llm)

    builder = StateGraph(AgentState)
    builder.add_edge(START, "supervisor")
    builder.add_node("supervisor", supervisor_node)
    builder.add_node("saving_node", saving_node)
    builder.add_node("search", tavily_node)

    for member in members:
        builder.add_edge(member, "supervisor")

    builder.add_conditional_edges("supervisor", lambda state: state["next"])
    builder.add_edge(START, "supervisor")

    graph = builder.compile()

    return graph


async def test(input: str):

    _, db = init_mongodb_client()
    graph = build_graph(db)

    input_dict = {
        "messages": [HumanMessage(content=input)],
        "next": None,
    }
    result = await graph.ainvoke(AgentState(**input_dict))

    print(result["messages"][-1].content)


if __name__ == "__main__":
    asyncio.run(
        test(
            "소나타 신형을 구매하고 싶은데, 100만원씩 저축하면 얼마나 걸릴까요? 사회초년생이고, 미혼에 자녀가 없습니다. 출산 계획도 없습니다."
        ))
