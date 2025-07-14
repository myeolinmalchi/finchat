from langchain_core.language_models import BaseChatModel
from langchain_core.messages import HumanMessage
from langchain_core.prompts import ChatPromptTemplate
from langgraph.config import get_stream_writer
from domains.saving.agents.graph_state import SavingGraphState


# TODO: Explain 에이전트 구현
def init_explain_node(llm: BaseChatModel):
    system = ChatPromptTemplate.from_messages([("system", "")])

    async def node(state: SavingGraphState):
        writer = get_stream_writer()
        blob = "\n".join([str(it) for it in state.get("selected", [])])
        resp = await llm.ainvoke(system.format_messages(content=blob))

        if not any(m.name == "title" for m in state["messages"]):
            writer({
                "chat_id": state["chat_id"],
                "status": "title",
                "content": {
                    "message": "군 장병 적금 상품 추천"
                }
            })
            state["messages"].append(HumanMessage(content="군 장병 적금 상품 추천",
                                                  name="title"))

        for chunk in chunk_text(resp.content):
            writer({
                "chat_id": state["chat_id"],
                "status": "response",
                "content": {
                    "message": chunk
                }
            })
        state["messages"].append(AIMessage(content=resp.content, name="explainer"))
        state["next"] = "refine"
        return state

    return node
