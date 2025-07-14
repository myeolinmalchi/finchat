from langchain_core.language_models import BaseChatModel
from langchain_core.prompts import ChatPromptTemplate


# TODO: Refine 에이전트 구현
def init_refine_node(llm: BaseChatModel):
    system = ChatPromptTemplate.from_messages([("system", "")])

    async def node(state: AgentState):
        writer = get_stream_writer()
        original = state["messages"][-1].content
        resp = await llm.ainvoke(system.format_messages(content=original))
        for chunk in chunk_text(resp.content):
            writer({
                "chat_id": state["chat_id"],
                "status": "response",
                "content": {
                    "message": chunk
                }
            })
        state["messages"].append(AIMessage(content=resp.content, name="refiner"))
        state["next"] = None
        return state

    return node
