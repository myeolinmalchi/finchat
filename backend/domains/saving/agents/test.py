# graph.py
"""금융 적금 상품 추천 에이전트 (LangGraph 기반)
다이어그램의 로직을 그대로 코드 구조로 옮겼다.
각 노드는 `init_XXX_node` 컨벤션으로 작성하여 DI(의존성 주입)가 쉽도록 설계했다.
"""

from __future__ import annotations

import operator
import uuid
from typing import List, Optional, TypedDict, Any

from langchain_core.language_models import BaseChatModel
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage
from langchain_core.tools import BaseTool
from langchain_core.prompts import ChatPromptTemplate

from langgraph.graph import StateGraph
from langgraph.prebuilt import create_react_agent
from langgraph.managed import RemainingSteps, IsLastStep


# ─────────────────────── 1. 공통 상태 정의 ───────────────────────
class AgentState(TypedDict):
    """그래프 전반에서 공유되는 상태"""

    messages: List[BaseMessage]  # 대화 기록
    tavily_results: Optional[dict]
    candidates: Optional[list]
    selected: Optional[list]
    offset: int  # pagination 용
    target_count: int  # 필요 추천 개수 (N)
    next: Optional[str]  # Supervisor 가 이용


# ─────────────────────── 2. 시스템 프롬프트 ───────────────────────
SYSTEM_PROMPT_SEARCH = """너는 국내 적금 상품에 정통한 재무 전문가다.
주어진 사용자의 요구 조건을 만족하는 적금 상품을 찾아라.
- 검색 도구를 반드시 사용한다.
- offset 은 페이지네이션 용으로 5 단위로 증가한다.
- 이미 선택된 상품을 중복으로 반환하지 않는다.
- JSON 형식으로 candidates 키에 최대 5개까지 상품을 배열로 담아 응답한다.
"""

SYSTEM_PROMPT_EXPLAIN = """너는 재무 컨설턴트다.
입력으로 주어진 적금 상품 리스트를 보고 각 상품을 사용자가 이해하기 쉽게 설명하라.
- 특징, 장단점, 추천 이유를 명확히 기술한다.
- 어려운 금융 용어는 최대한 배제한다.
- markdown bullet list 로 정리한다.
"""

SYSTEM_PROMPT_REFINE = """아래 설명에서 전문 용어·불필요한 반복을 줄이고, 한글 맞춤법을 교정하라.
결과는 동일한 markdown 형식을 유지한다.
"""

# ─────────────────────── 3. 노드 정의 ───────────────────────


def init_search_tool_select_node(tools: List[BaseTool]):
    """검색 도구 선택 노드 (단순히 첫 번째 도구를 사용하도록 설정)"""

    async def node(state: AgentState):
        # 현 예시에서는 tools[0] 하나만 사용
        state["next"] = "saving_search"
        return state

    return node


def init_saving_search_node(
    llm: BaseChatModel,
    tools: List[BaseTool],
    prompt: str = SYSTEM_PROMPT_SEARCH,
):
    """적금 검색 노드"""

    agent = create_react_agent(llm, tools, prompt=prompt)

    async def node(state: AgentState):
        result = await agent.ainvoke({
            "messages": state["messages"],
            "offset": state["offset"],
        })
        # 결과는 {'candidates': [...], 'messages': [...] } 형태를 기대
        state.setdefault("candidates", []).extend(result.get("candidates", []))
        # tool 호응 메시지도 기록
        if result.get("messages"):
            state["messages"].append(
                HumanMessage(content=result["messages"][-1].content,
                             name="saving_agent"))
        state["next"] = "filter"
        return state

    return node


def init_filter_node():
    """조건 필터링 노드 – 예시는 패스스루. 실제 로직은 상황에 맞게 구현."""

    async def node(state: AgentState):
        # 실제 구현: state["candidates"] 리스트에서 조건에 맞는 항목만 선별
        filtered = state.get("candidates", [])  # placeholder
        state.setdefault("selected", []).extend(filtered)
        state["candidates"] = []  # candidates 비우기
        state["next"] = "router"
        return state

    return node


def init_router_node():
    """Router – 선택된 상품이 목표 개수 이상인지 판단, 부족하면 offset 증가 후 재탐색"""

    async def node(state: AgentState):
        if len(state.get("selected", [])) >= state["target_count"]:
            state["next"] = "supervisor"
        else:
            state["offset"] += 5
            state["next"] = "search_tool_select"
        return state

    return node


def init_tavily_node(tavily_tool: BaseTool):
    """웹 기반 외부 데이터 검색"""

    async def node(state: AgentState):
        query = ", ".join([item.get("name", "") for item in state.get("selected", [])])
        tavily_result = tavily_tool.invoke({"query": query})  # sync 예시
        state["tavily_results"] = tavily_result
        state["next"] = "explain"
        return state

    return node


def init_explain_node(llm: BaseChatModel, prompt: str = SYSTEM_PROMPT_EXPLAIN):
    """각 상품에 대한 설명 작성 노드"""

    system = ChatPromptTemplate.from_messages([("system", prompt)])

    async def node(state: AgentState):
        items = state.get("selected", [])
        content = "\n".join([str(it) for it in items])
        resp = await llm.ainvoke(system.format_messages(content=content))
        state["messages"].append(AIMessage(content=resp.content, name="explainer"))
        state["next"] = "refine"
        return state

    return node


def init_refine_node(llm: BaseChatModel, prompt: str = SYSTEM_PROMPT_REFINE):
    """설명 다듬기 노드"""

    system = ChatPromptTemplate.from_messages([("system", prompt)])

    async def node(state: AgentState):
        last_msg = state["messages"][-1].content  # 방금 explain 내용
        refined = await llm.ainvoke(system.format_messages(content=last_msg))
        state["messages"].append(AIMessage(content=refined.content, name="refiner"))
        state["next"] = None  # 종료
        return state

    return node


def init_supervisor_node():
    """Supervisor – 어디로 갈지 지휘"""

    async def node(state: AgentState):
        # 이미 외부 데이터가 없다면 tavily 부터, 그 다음 explain/refine 순
        if state.get("tavily_results") is None:
            state["next"] = "tavily"
        elif any(msg.name == "explainer" for msg in state["messages"]):
            # explain 이 끝난 뒤엔 refine 이 호출됨, refine 끝나면 종료
            if any(msg.name == "refiner" for msg in state["messages"]):
                state["next"] = None
            else:
                state["next"] = "refine"
        else:
            state["next"] = "explain"
        return state

    return node


# ─────────────────────── 4. 그래프 컴파일러 ───────────────────────


def build_graph(
    llm: BaseChatModel,
    saving_tools: List[BaseTool],
    tavily_tool: BaseTool,
    target_count: int = 5,
):
    """그래프 빌더 함수 – 외부 의존성 주입 후 StateGraph 반환"""

    sg = StateGraph(AgentState)

    # 노드 등록
    sg.add_node("search_tool_select", init_search_tool_select_node(saving_tools))
    sg.add_node("saving_search", init_saving_search_node(llm, saving_tools))
    sg.add_node("filter", init_filter_node())
    sg.add_node("router", init_router_node())
    sg.add_node("tavily", init_tavily_node(tavily_tool))
    sg.add_node("explain", init_explain_node(llm))
    sg.add_node("refine", init_refine_node(llm))
    sg.add_node("supervisor", init_supervisor_node())

    # 에지 정의
    sg.add_edge("search_tool_select", "saving_search")
    sg.add_edge("saving_search", "filter")
    sg.add_edge("filter", "router")

    sg.add_conditional_edges(
        "router",
        lambda state: state["next"],
        {
            "supervisor": "supervisor",
            "search_tool_select": "search_tool_select",
        },
    )

    sg.add_edge("supervisor", "tavily")
    sg.add_edge("tavily", "explain")
    sg.add_edge("explain", "refine")
    sg.add_edge("refine", "supervisor")

    # start 및 done 설정
    sg.set_entry_point("search_tool_select")
    sg.set_finish_point(lambda state: state.get("next") is None)

    graph = sg.compile()

    # 초기 상태 팩토리
    def invoke(user_msg: str):
        return graph.invoke({
            "messages": [HumanMessage(content=user_msg)],
            "tavily_results": None,
            "candidates": [],
            "selected": [],
            "offset": 0,
            "target_count": target_count,
            "next": "search_tool_select",
        })

    # graph, helper 함수 반환
    return graph, invoke


# ─────────────────────── 5. 사용 예제 ───────────────────────
if __name__ == "__main__":
    from langchain_openai import ChatOpenAI
    from langchain_tavily import TavilySearchTool

    llm = ChatOpenAI(model="gpt-4o-mini")

    # 예시용 도구 – 실제 구현은 saving API 호출 함수로 교체
    async def dummy_saving_search(monthly_deposit: int,
                                  total_term_months: int,
                                  offset: int = 0,
                                  top_k: int = 5):
        return {"candidates": [{"name": f"Saving-{uuid.uuid4()}", "rate": 3.5}]}

    saving_tool = BaseTool.from_function(
        name="find_savings",
        description="적금 상품 검색",
        func=dummy_saving_search,
        sync=True,
    )

    tavily_tool = TavilySearchTool()

    graph, run = build_graph(llm, [saving_tool], tavily_tool)

    result_state: AgentState = run("50만원씩 적금해서 1200만원 모으고 싶은데 추천해줘")
    for msg in result_state["messages"]:
        if isinstance(msg, (AIMessage, HumanMessage)):
            print(f"{msg.name or 'assistant'}: {msg.content}")
