from typing import List
from langchain_core.language_models import BaseChatModel
from langchain_core.tools import BaseTool
from langgraph.config import get_stream_writer

from domains.saving.agents.graph_state import SavingGraphState

import json


def init_saving_tool_seleciton_node(llm: BaseChatModel, tools: List[BaseTool]):
    """검색 Tool 및 파라미터 결정"""
    agent_with_tools = llm.bind_tools(tools)

    async def node(state: SavingGraphState):
        writer = get_stream_writer()
        writer({
            "chat_id": state["chat_id"],
            "status": "pending",
            "content": {
                "message": "기준 금리를 확인하고 있습니다."
            }
        })

        res = await agent_with_tools.ainvoke(state["messages"])

        tool_call = res.additional_kwargs["tool_calls"][0]
        state["tool"] = {
            "tool_name": tool_call["function"]["name"],
            "tool_args": json.loads(tool_call["function"].get("arguments", "{}")),
        }

        state["messages"].append(res)
        state["next"] = "tool_node"
        return state

    return node
