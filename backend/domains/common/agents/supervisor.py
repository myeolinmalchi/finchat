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
