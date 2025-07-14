from domains.common.agents.states import AgentState


# TODO: Tavily 검색 노드 구현
def init_tavily_node(tavily_tool: BaseTool):

    async def node(state: AgentState):
        query = ", ".join([p.get("name", "") for p in state.get("selected", [])])
        state["tavily_results"] = tavily_tool.invoke({"query": query})
        state["next"] = "explain"
        return state

    return node
