from typing import List, Dict
from langchain_core.tools import BaseTool
from langgraph.config import get_stream_writer

from domains.saving.agents.graph_state import SavingGraphState


def init_tool_execution_node(tools: List[BaseTool]):
    """선택된 Tool을 실제로 실행하는 노드"""

    tool_map: Dict[str, BaseTool] = {t.name: t for t in tools}

    async def node(state: SavingGraphState):
        writer = get_stream_writer()

        tool_ = state["tool"]

        if not tool_:
            raise ValueError("검색 도구가 선택되지 않았습니다.")

        tool_name = tool_["tool_name"]
        tool_args = tool_["tool_args"]

        tool = tool_map.get(tool_name)
        if tool is None:
            raise ValueError(f"존재하지 않는 도구입니다: {tool_name}")

        # 동기·비동기 호출 구분
        if getattr(tool, "sync", False):
            result: Any = tool.invoke(tool_args)  # type: ignore[arg-type]
        else:
            result = await tool.ainvoke(tool_args)

        if isinstance(result, dict) and "candidates" in result:
            # TODO: `SavingSearchResult` 인스턴스로 파싱 필요
            state.setdefault("candidates", []).extend(result)

        # TODO: 스트림 출력 추가 (pending, analysis)
        writer({})

        state["next"] = "filter"
        return state

    return node
