import json
from typing import List
from dotenv import load_dotenv
from openai import AsyncOpenAI
from pydantic import TypeAdapter

from common.decorators.asyncio import retry_async
from domains.saving.models import BaseInterestRateTier, SavingPreferentialRate

import os
import asyncio

load_dotenv()

UPSTAGE_API_KEY = os.getenv("UPSTAGE_API_KEY", "")

saving_preferential_rate_response_format = {
    "type": "json_schema",
    "json_schema": {
        "name": "saving_preferential_rate",
        "strict": True,
        "schema": {
            "type": "array",
            "description": "우대금리 조건 목록",
            "items": {
                "type": "object",
                "properties": {
                    "description": {
                        "type": "string"
                    },
                    "rate_type": {
                        "type": "string",
                        "enum": ["user_choice", "pre_condition", "event_based"]
                    },
                    "tiers": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "condition": {
                                    "type": "string"
                                },
                                "interest_rate": {
                                    "type": "number",
                                    "description": "연 금리(%p)"
                                }
                            },
                            "required": ["condition", "interest_rate"]
                        }
                    }
                },
                "required": ["description", "rate_type", "tiers"]
            }
        }
    }
}

PREFERENTIAL_INTEREST_RATE_AGENT_SYSTEM_PROMPT = (
    "당신은 적금 데이터 추출 어시스턴트입니다.\n"
    "주어지는 입력은 적금 상품의 우대금리 안내문입니다.\n"
    "제공된 JSON 스키마를 충족하는 구조화 데이터를 반환하세요.\n"
    "정확한 이율 값이 포함되지 않은 경우에는 `tiers`를 빈 배열로 반환합니다.")


@retry_async(times=20, delay=1)
async def extract_saving_preferential_rates(
        client: AsyncOpenAI,
        raw_text: str,
        model: str = "solar-pro") -> List[SavingPreferentialRate]:
    """
    우대금리 원문에서 SavingPreferentialRate 리스트를 추출한다.

    Args:
        client (AsyncOpenAI): OpenAI 비동기 클라이언트
        raw_text (str): 우대금리 설명이 포함된 원문
        model (str): 사용할 모델

    Returns:
        List[SavingPreferentialRate]: 파싱된 우대금리 정보
    """
    response = await client.chat.completions.create(
        model=model,
        messages=[
            {
                "role": "system",
                "content": PREFERENTIAL_INTEREST_RATE_AGENT_SYSTEM_PROMPT
            },
            {
                "role": "user",
                "content": raw_text
            },
        ],
        response_format=saving_preferential_rate_response_format,  # type: ignore
        max_tokens=8192,
    )

    content = response.choices[0].message.content

    if not content:
        raise ValueError("잘못된 응답입니다.")

    data = json.loads(content, strict=False)

    return TypeAdapter(List[SavingPreferentialRate]).validate_python(data)


base_rate_response_format = {
    "type": "json_schema",
    "json_schema": {
        "name": "base_interest_rates",
        "strict": True,
        "schema": {
            "type": "array",
            "description": "가입 기간 구간별 기본 금리 목록",
            "items": {
                "type": "object",
                "properties": {
                    "min_term": {
                        "type": "integer",
                        "description": "구간 하단(포함), 단위: month"
                    },
                    "max_term": {
                        "type": "integer",
                        "description": "구간 상단(미포함). -1 → 상한 없음"
                    },
                    "interest_rate": {
                        "type": "number",
                        "description": "해당 구간의 연 금리(%p)"
                    }
                },
                "required": ["min_term", "interest_rate"]
            }
        }
    }
}

BASE_INTEREST_RATE_SYSTEM_PROMPT = ("당신은 금융 데이터 추출 어시스턴트입니다.\n"
                                    "주어진 표 데이터에 포함된 '기간별 만기 이율'에 대하여 "
                                    "가입 기간 범위와 연 금리를 추출해야 한다.\n\n"
                                    "다음 규칙을 반드시 따라야 한다.\n"
                                    "1. 기간이 'N개월 이상 M개월 미만' -> min_term=N, max_term=M\n"
                                    "2. 'N개월 이상' -> min_term=N, max_term=null\n"
                                    "3. 'N년만기' -> min_term=N*12, max_term=N*12\n"
                                    "4. 금리는 '%', 'p' 등 기호를 제거하고 float로 반환\n\n"
                                    "주어진 JSON Schema를 정확히 준수해라.")


@retry_async(times=20, delay=1)
async def extract_base_interest_rate_tiers(
    client: AsyncOpenAI,
    html_snippet: str,
    model: str = "solar-pro2",
) -> List[BaseInterestRateTier]:
    """
    HTML 테이블에서 기본 금리 구간을 추출한다.

    Args:
        client (AsyncOpenAI): OpenAI 비동기 클라이언트
        html_snippet (str): <table> 태그를 포함한 HTML 부분
        model (str): 사용할 모델명

    Returns:
        List[BaseInterestRateTier]: 구간별 기본 금리 정보
    """
    resp = await client.chat.completions.create(
        model=model,
        temperature=0.3,
        reasoning_effort="medium",
        messages=[
            {
                "role": "system",
                "content": BASE_INTEREST_RATE_SYSTEM_PROMPT
            },
            {
                "role": "user",
                "content": html_snippet
            },
        ],
        response_format=base_rate_response_format,  # type: ignore
        max_tokens=8192,
    )

    content = resp.choices[0].message.content

    if not content:
        raise ValueError("잘못된 응답입니다.")

    data = json.loads(content, strict=False)

    return TypeAdapter(List[BaseInterestRateTier]).validate_python(data)


if __name__ == "__main__":
    text = """\
    모바일뱅킹 첫거래 고객: 상품 가입 전 최근 1개월 이내 ① 또는 ②에 해당하는 고객
    1. 모바일뱅킹 최초 신규고객
    2. 장기 미사용으로 인한 모바일뱅킹 정지 해제한 고객
    ※ 모바일뱅킹 해지한 고객이 신규한 경우는 포함되지 않습니다. : 0.1%
    """
    client = AsyncOpenAI(
        api_key=UPSTAGE_API_KEY,
        base_url="https://api.upstage.ai/v1",
    )

    result = asyncio.run(extract_saving_preferential_rates(client=client,
                                                           raw_text=text))

    print(result)

    base_text = """\
    <table class=\"InterestRateTable_table__jAfYr\">\n <caption class=\"blind\">\n  기본 금리\n </caption>\n <thead>\n  <tr>\n   <th scope=\"col\">\n    기간\n   </th>\n   <th scope=\"col\">\n    금리\n   </th>\n  </tr>\n </thead>\n <tbody>\n  <tr>\n   <th class=\"InterestRateTable_cell__QR7x_ InterestRateTable_row-head__ejfZd\" scope=\"row\">\n    <p>\n     1년만기\n    </p>\n   </th>\n   <td class=\"InterestRateTable_cell__QR7x_\">\n    3.000%\n   </td>\n  </tr>\n </tbody>\n</table>\n
    """

    result = asyncio.run(
        extract_base_interest_rate_tiers(client=client, html_snippet=base_text))

    print(result)
