from typing import AsyncIterator, List, Optional, Protocol, TypedDict, cast
from langchain_core.language_models import BaseChatModel
from langchain_core.messages import AIMessage, BaseMessage, HumanMessage
from langchain_core.runnables import RunnableConfig
from langchain_openai.chat_models.base import ChatOpenAI
from langchain_upstage import ChatUpstage
from langgraph.config import get_stream_writer
from langgraph.graph import END, StateGraph
from motor.motor_asyncio import AsyncIOMotorDatabase
from domains.chat.models import Chat, ChatProductInfo
from domains.common.agents.graph_state import GraphState, PlanWithGoals
from domains.common.agents.retrieval_subgraph.retrieval_node import init_retrieval_node, init_retrieval_subgraph
from domains.common.agents.types import Members
from domains.saving.agents.explain_node import init_explain_node
from domains.saving.agents.saving_subgraph import init_saving_subgraph
from domains.saving.agents.tool_factory import init_saving_retrieval_tools
from domains.saving.repositories.retrieval import get_saving_by_ids
from domains.user.models import UserMemory
from domains.user.services import UserMemoryService

SUPERVISOR_SYSTEM_PROMPT = """\
<Role>
당신은 Supervisor Node로서 "적금 추천" 전체 워크플로우를 계획하고 실행까지 조율한다.
</Role>

<Goal>
1. 사용자의 요구·제약·데이터 부족 여부를 분석해 하위 노드 실행 순서를 결정
   - 상품 가격, 금리 추이 등의 외부 지식 정보가 필요한 경우 ->research_node 포함
   - 상품 검색이 필요한 경우 -> saving_node -> explain_node
   - 이전 대화 맥락만으로 충분한 경우 -> explain_node 단독 호출

2. JSON 형태로 {"plan":[...], "next":"..."} 반환
</Goal>

<Nodes>
- research_node: 외부 정보 탐색을 위한 리서치 노드
- saving_node: 적합한 적금 상품을 검색하기 위한 적금 노드
- explain_node: 최종 응답을 생성하기 위한 설명 노드
<Nodes>

<Examples>
### Example 1:
질문:
"6개월만 넣고, 중도해지해도 불이익 없는 적금 상품 있을까?"

{
  "plans": [
    {
      "member": "saving_node",
      "goal": "사용자의 조건(6개월, 중도해지 시 불이익 없음)을 만족하는 적금 상품 검색"
    },
    {
      "member": "explain_node",
      "goal": "검색된 상품의 조건과 장단점을 사용자에게 설명"
    }
  ],
  "next": "saving_node"
}

### Example 2:
질문:
"요즘 금리가 오르고 있다던데, 금리 높은 적금 상품 추천해줘"

{
  "plans": [
    {
      "member": "research_node",
      "goal": "최근 기준 금리 및 시중 금리 동향 파악"
    },
    {
      "member": "saving_node",
      "goal": "금리 동향과 사용자 요구에 기반해 높은 금리의 적금 상품 검색"
    },
    {
      "member": "explain_node",
      "goal": "추천된 적금 상품의 금리 및 조건을 사용자에게 설명"
    }
  ],
  "next": "research_node"
}

### Example 3:
질문:
"아까 추천해준 상품 다시 설명해줘"

{
  "plans": [
    {
      "member": "explain_node",
      "goal": "이전에 추천한 적금 상품에 대해 다시 설명"
    }
  ],
  "next": "explain_node"
}
</Examples>"""


def init_supervisor_node(llm: BaseChatModel):

    class SupervisorResponse(TypedDict):
        plans: List[PlanWithGoals]
        next: Members

    async def supervisor_node(state: GraphState):
        print("============ Supervisor Node ============")

        writer = get_stream_writer()

        # 1) 이미 계획이 있으면 다음 단계만 실행
        if "plans" in state and state["current_step"] < len(state["plans"]):
            next_ = state["plans"][state["current_step"]]
            return {"next": next_, "current_step": state["current_step"] + 1}

        writer({
            "chat_id": state["chat_id"],
            "status": "pending",
            "content": {
                "message": "리서치 계획을 수립하고 있습니다."
            }
        })

        # 2) 최초 호출 → 계획 수립
        messages = [
            {
                "role": "system",
                "content": SUPERVISOR_SYSTEM_PROMPT
            },
            *state["messages"],
        ]
        result = cast(
            SupervisorResponse, await
            llm.with_structured_output(SupervisorResponse).ainvoke(messages))

        print(result["plans"])

        return {"next": result["plans"][0], "plans": result["plans"], "current_step": 1}

    return supervisor_node


class StreamGraphType(Protocol):

    def __call__(self,
                 user_msg: str,
                 curr_chat: Chat,
                 memories: List[UserMemory],
                 config: Optional[RunnableConfig] = ...) -> AsyncIterator[dict]:
        ...


def init_graph(
    llm: BaseChatModel,
    db: AsyncIOMotorDatabase,
    target_count: int = 3,
) -> StreamGraphType:
    sg = StateGraph(GraphState)

    llm_with_reasoning = ChatOpenAI(
        model="gpt-5",
        reasoning_effort="low",
        #temperature=0.3,
    )
    """
    llm_with_reasoning = ChatUpstage(
        model="solar-pro2",
        temperature=0.3,
        reasoning_effort="high",
        max_tokens=16384,
    )
    """

    saving_col = db.get_collection("savings")

    saving_tools = init_saving_retrieval_tools(saving_col)
    sg.add_node("saving_node", init_saving_subgraph(llm, saving_tools))

    _retrieval_subgraph = init_retrieval_subgraph()
    _retrieval_node = init_retrieval_node(_retrieval_subgraph)

    #sg.add_node("research_node", init_research_node(llm))
    sg.add_node("research_node", _retrieval_node)

    sg.add_node("explain_node", init_explain_node(llm))

    sg.add_node("supervisor", init_supervisor_node(llm_with_reasoning))

    sg.add_edge("research_node", "supervisor")
    sg.add_edge("saving_node", "supervisor")
    sg.add_edge("explain_node", END)

    sg.add_conditional_edges("supervisor", lambda s: s["next"]["member"])

    sg.set_entry_point("supervisor")

    graph = sg.compile()

    async def stream_graph(
            user_msg: str,
            curr_chat: Chat,
            memories: List[UserMemory] = [],
            config: Optional[RunnableConfig] = None) -> AsyncIterator[dict]:

        products: List[ChatProductInfo] = []
        prev_messages: List[BaseMessage] = []

        if curr_chat.messages:
            # 마지막 추천 상품을 전역 시스템 프롬프트에 추가
            products = list(
                filter(lambda msg: msg.role == "assistant",
                       curr_chat.messages))[-1].content.products or []

            # 이전 대화 내역 convert (products 제외)
            prev_messages = list(
                map(
                    lambda msg: HumanMessage(content=msg.content.message or "")
                    if msg.role == "assistant" else AIMessage(
                        content=msg.content.message or ""), curr_chat.messages))

        saving_ids = [p.product_id for p in products if p.product_id]
        savings = await get_saving_by_ids(saving_col, saving_ids)

        init_state: GraphState = {
            "chat_id": curr_chat.id,
            "messages": [*prev_messages, HumanMessage(content=user_msg)],
            "documents": [],
            "candidates": [],
            "selected": savings,
            "offset": 0,
            "target_count": target_count + len(savings),
            "next": None,
            "plans": [],
            "current_step": 0,
            "user_info": None,
            "user_memories": memories,
        }
        async for chunk in graph.astream(init_state,
                                         stream_mode="custom",
                                         subgraphs=True,
                                         config=config):
            yield chunk

    return stream_graph
