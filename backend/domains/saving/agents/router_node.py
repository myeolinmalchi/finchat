from domains.saving.agents.graph_state import SavingGraphState


def init_router_node():

    async def node(state: SavingGraphState):
        # 선택한 상품 수가 target_count개 이상일 때
        if len(state.get("selected", [])) >= state["target_count"]:
            state["next"] = "supervisor"
        else:
            state["offset"] += 5
            state["next"] = "tool_selector"
        return state

    return node
