from typing import Annotated, List, TypedDict
from langchain_core.language_models import BaseChatModel
from langchain_core.messages import BaseMessage, HumanMessage
from langchain_core.tools import BaseTool

from langgraph.managed import IsLastStep, RemainingSteps
from langgraph.prebuilt import create_react_agent
from pydantic import BaseModel

from domains.common.agents.states import AgentState

SYSTEM_PROMPT = """\
너는 국내 적금 상품에 정통한 재무 전문가 에이전트다.
Goal: 사용자의 조건을 만족하는 적금 상품 5개를 찾아 추천 목록을 완성한다.

Tool Calling Instructions:
- 반드시 검색 도구 중 하나를 사용하라.
- Parameters:
    • monthly_deposit: 사용자가 월 납입을 원하는 금액 (원)  
    • total_term_months: 적금 기간 (개월)  
    • offset: 5 단위로 증가하며 페이지네이션에 사용 (기본값: 0)
    • top_k: 한 번에 가져올 최대 개수 (기본값: 5)
- 검색 도구가 반환하는 SavingSearchResult에 다음 필드를 활용해 필터링하라: 
    • product.base_interest_rate  
    • product.max_interest_rate  
    • product.institution.name 등

행동 규칙:
1. **Thought → Action(find_savings) → Action Input → Observation** 사이클을 반복한다.  
2. Observation 리스트를 순회하며 조건 불충족 상품은 폐기한다.  
3. 사용자의 조건과 일치하지 않으며, 가입이 불가능한 상품은 반드시 제외한다.
4. 사용자가 가입 가능한 상품의 개수가 5개 이상이면 루프를 종료한다.
5. 추가 검색이 필요한 경우 offset값을 5만큼 늘려서 재검색한다.
6. Observation이 빈 리스트일 때도 루프를 종료한다.
7. 중복 상품은 저장하지 않는다.

Final Answer:
• 조건에 부합하는 추천 상품에 대한 전체 레포트.
• 검색을 어떤식으로 수행했는지에 대한 설명과, 명료한 근거 
• 상품에 대한 설명은 한 상품당 세 문장 이상, 한 문단으로 구성되어야 하며, 모든 상품에 대해 빠짐없이 작성해야 함.
• 설명: 각 상품에 대한 대략적인 요약과, 어떤 점에서 강점을 가지는지, 그리고 왜 추천하는지에 대한 친절한 설명.
• 사용자의 원래 질문에 대해 어떤식으로 참고할 수 있고, 어떤 도움이 되는지에 대한 개별적인 설명

반드시 Thought/Action/Action Input/Observation/Final Answer 패턴을 지켜라."""

import operator


class SavingProduct(BaseModel):
    name: str
    institution: str
    base_rate: float
    max_rate: float
    pros: List[str]
    cons: List[str]
    features: List[str]
    recommended_reason: str


class SavingRecommendation(BaseModel):

    products: List[SavingProduct]


class SavingAgentState(TypedDict):
    messages: Annotated[List[BaseMessage], operator.add]
    selected: List[dict]
    offset: int
    target_count: int

    is_last_step: IsLastStep
    remaining_steps: RemainingSteps


def bump_offset(state: SavingAgentState) -> dict:

    last = state["messages"][-1]
    if getattr(last, "tool_calls", None):
        return {"offset": state["offset"] + 5}

    return {}


def init_saving_search_node(llm: BaseChatModel,
                            tools: List[BaseTool],
                            prompt: str = SYSTEM_PROMPT):
    """적금 검색 노드"""

    #prompt_template = PromptTemplate.from_template(prompt)

    agent = create_react_agent(llm, tools, prompt=prompt)

    #state_schema=SavingAgentState)
    #post_model_hook=bump_offset)
    async def node(state: AgentState):
        result = await agent.ainvoke({
            "messages": state["messages"],
            #"selected": [],
            #"offset": 0,
            #"target_count": 5,
        })
        return {
            "messages": [
                HumanMessage(content=result["messages"][-1].content,
                             name="saving_agent")
            ],
            "next": "supervisor"
        }

    return node
