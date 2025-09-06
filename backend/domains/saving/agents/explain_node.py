from typing import List
from langchain_core.language_models import BaseChatModel
from langchain_core.messages import AIMessage
from langchain_core.prompts import ChatPromptTemplate, HumanMessagePromptTemplate, SystemMessagePromptTemplate
from langchain_openai.chat_models.base import ChatOpenAI
from langgraph.config import get_stream_writer
from langgraph.graph import END

from domains.common.agents.graph_state import GraphState
from domains.saving.agents.prompts import (SAVING_EXPLAIN_NODE_SYSTEM_PROMPT,
                                           SAVING_EXPLAIN_USER_PROMPT_TEMPLATE)


def init_explain_node(llm: BaseChatModel):

    llm = ChatOpenAI(model="gpt-4.1", temperature=0.3)

    async def node(state: GraphState):
        writer = get_stream_writer()

        print("============ Explain Node ============")

        prompt_template = ChatPromptTemplate.from_messages([
            SystemMessagePromptTemplate.from_template(
                SAVING_EXPLAIN_NODE_SYSTEM_PROMPT), *state["messages"],
            HumanMessagePromptTemplate.from_template(
                SAVING_EXPLAIN_USER_PROMPT_TEMPLATE)
        ])

        products = state["selected"]

        research_blob = "\n\n## 외부 참고 정보\n" + "\n".join(
            f"- {d}" for d in state["documents"])

        combined_memories = "\n".join([m.content for m in state["user_memories"]])

        if products:

            blob: str = "\n---\n".join(map(str, products))

            prompt = prompt_template.invoke({
                "user_memories": combined_memories,
                "product_info": blob,
                "context": research_blob,
                "user_question": str(state["messages"][0].content),
            })

            writer({
                "chat_id": state["chat_id"],
                "status": "response",
                "content": {
                    "products": [{
                        "name": p.product.name,
                        "product_id": p.product.id,
                        "product_type": "saving",
                        "options": p.product.format_interest_rates(),
                        "institution": p.product.institution,
                        "description": p.product.name,
                        "details": str(p.product),
                        "tags": [],
                    } for p in products]
                }
            })

        else:

            prompt = prompt_template.invoke({
                "user_memories": combined_memories,
                "product_info": "NONE",
                "context": research_blob,
                "user_question": str(state["messages"][0].content),
            })

        chunks: List[str] = []
        async for chunk in llm.astream(prompt):
            chunk_content = str(chunk.content)
            chunks.append(chunk_content)
            writer({
                "chat_id": state["chat_id"],
                "status": "response",
                "content": {
                    "message": chunk_content
                }
            })

        writer({
            "chat_id": state["chat_id"],
            "status": "stop",
        })

        content = "".join(chunks)

        state["messages"].append(AIMessage(content=content, name="explainer"))
        state["next"] = {"member": END}  # type: ignore

        return state

    return node
