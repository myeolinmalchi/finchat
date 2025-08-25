from typing import Dict, List, Any, Literal, Optional, TypedDict, cast
from langchain_core.language_models import BaseChatModel
from langchain_core.messages import BaseMessage
from langchain_core.prompts import (
    ChatPromptTemplate,
    SystemMessagePromptTemplate,
    HumanMessagePromptTemplate,
)
from langchain_core.runnables import (
    RunnableLambda,
    RunnableMap,
)

from kss import Kss

from domains.user.agents.prompts import MEMORY_EXTRACT_HUMAN_PROMPT, MEMORY_EXTRACT_SYSTEM_PROMPT
from domains.user.services import UserMemoryService
from domains.user.models import UserMemory

system_prompt = SystemMessagePromptTemplate.from_template(MEMORY_EXTRACT_SYSTEM_PROMPT)
human_prompt = HumanMessagePromptTemplate.from_template(MEMORY_EXTRACT_HUMAN_PROMPT)

prompt = ChatPromptTemplate.from_messages([system_prompt, human_prompt])


class MemoryExtractionOutput(TypedDict):
    content: Optional[str]
    category: Literal["goal", "income", "risk_profile", "experience", "preference",
                      "etc"]
    metadata: Dict


split_sentences = Kss("split_sentences")


def build_memory_extraction_chain(
    *,
    llm: BaseChatModel,
    memory_service: UserMemoryService,
):

    InputType = TypedDict("InputType", {"user_id": str, "messages": List[BaseMessage]})
    CleanedInputType = TypedDict("CleanedInputType", {
        "user_id": str,
        "conversation": str,
        "memories": str
    })

    async def prepare_input(inputs: InputType) -> CleanedInputType:
        print("메모리 추출을 시도합니다.")

        user_id: str = inputs["user_id"]
        conversation: str = "\n".join(
            f"{m.type.capitalize()}: {m.content}" for m in inputs["messages"])

        memories: List[UserMemory] = await memory_service.list_memories(user_id=user_id,
                                                                        limit=100)

        memory_str = "\n".join(f"- {m.content}" for m in memories)

        return {
            "user_id": user_id,
            "conversation": conversation,
            "memories": memory_str,
        }

    LLMOutput = TypedDict("LLMOutput", {"input": InputType, "raw": Any})

    async def post_process(data: LLMOutput) -> UserMemory | None:

        parsed_output = cast(MemoryExtractionOutput, data["raw"]["parsed"])

        if "content" not in parsed_output or not parsed_output["content"]:
            print("추출된 메모리가 없습니다.")
            return None

        print("before: ", parsed_output["content"])

        contents: List[str] = split_sentences(parsed_output["content"])
        combined = "\n".join(contents)

        print("after: ", combined)

        created = await memory_service.add_memory(
            user_id=data["input"]["user_id"],
            #content=parsed_output["content"],
            content=combined,
            category=parsed_output["category"],
            metadata=parsed_output["metadata"],
        )

        return created

    def _dummy(_) -> UserMemory:
        raise NotImplementedError

    chain = RunnableMap({
        "raw": (RunnableLambda(prepare_input) | prompt |
                llm.with_structured_output(MemoryExtractionOutput, include_raw=True)),
        "input": lambda input: input
    }) | RunnableLambda(func=_dummy, afunc=post_process)

    return chain
