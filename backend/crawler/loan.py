"""대출상품 크롤러"""

import re
from typing import List, Optional

from pgvector import SparseVector
from selenium.webdriver.common.by import By

from crawler.base import BASE_URL, SeleniumClient, BaseKBCrawler

import time

import requests

from bs4 import BeautifulSoup

from db.common import V_DIM
from db.models.loan import LoanModel, LoanChunkModel
from preprocess.html import clean_html

from pydantic import BaseModel

from utils.embed import create_embedding


class LoanDTO(BaseModel):
    url: str

    title: str
    contents: List[str]
    description: str

    category: Optional[str] = None

    target: Optional[str] = None
    period: Optional[str] = None
    repayment_method: Optional[str] = None
    limit: Optional[str] = None


class LoanCrawler(BaseKBCrawler[LoanDTO, LoanModel], SeleniumClient):

    def scrape_urls(self, page_code):

        print(f"[{page_code}] 대출 상품 목록 불러오는중...")

        url = f"https://obank.kbstar.com/quics?page={page_code}#CP"

        self.driver.get(url)

        time.sleep(10)

        tot_codes: List[str] = []

        for element in self.pagination_generator():
            element.click()

            time.sleep(5)

            selector = "ul.list-product1 > li > div.area1 > a"
            loans = self.driver.find_elements(by=By.CSS_SELECTOR, value=selector)
            onclicks = [loan.get_attribute("onclick") for loan in loans]
            onclicks = [onclick for onclick in onclicks if onclick is not None]
            codes = [parse_loan_code(onclick) for onclick in onclicks]
            codes = [code for code in codes if code is not None]

            tot_codes += codes

        url_factory = "{}/quics?page={}&cc=b104363:b104516&isNew=N&prcode={}&QSL=F"
        urls = [url_factory.format(BASE_URL, page_code, code) for code in tot_codes]

        return urls

    def dto2orm(self, dto):

        if not dto.category:
            raise ValueError("`LoanDTO` must be include `category` property")

        orm = LoanModel()

        orm.url = dto.url
        orm.title = dto.title
        orm.category = dto.category
        orm.description = dto.description

        basic_info = (
            f"대상: {dto.target if dto.target else "NONE"}\n"
            f"기간: {dto.period if dto.period else "NONE"}\n"
            f"상환방법: {dto.repayment_method if dto.repayment_method else "NONE"}\n"
            f"한도: {dto.limit if dto.limit else "NONE"}\n"
            "---\n"
        )

        for idx, content in enumerate(dto.contents):
            dto.contents[idx] = basic_info + content

        if dto.target:
            orm.target = dto.target

        if dto.period:
            orm.period = dto.period

        if dto.repayment_method:
            orm.repayment_method = dto.repayment_method

        if dto.limit:
            orm.limit = dto.limit

        print("임베딩 하는중 ...")
        embeddings = create_embedding(dto.contents, html=True, chunking=False)

        chunks = [
            LoanChunkModel(
                content=content,
                dense_vector=emb.dense,
                sparse_vector=SparseVector(emb.sparse, V_DIM),
            ) for content, emb in zip(dto.contents, embeddings)
        ]

        orm.chunks = chunks

        return orm

    def scrape_detail(self, url):
        print(f"대출상품 크롤링 하는중... ({url})")

        res = requests.get(url)
        res.raise_for_status()

        soup = BeautifulSoup(res.text)

        dto_dict = {}
        dto_dict["url"] = url

        title_element = soup.select_one("div.product-basic > h2.headline > b")
        description_element = soup.select_one("div.product-basic > h2.headline > span")

        if not title_element or not description_element:
            return None

        dto_dict["title"] = title_element.get_text("", strip=True)
        dto_dict["description"] = description_element.get_text("", strip=True)

        content_elements = soup.select("div.blockBox")

        dto_dict["contents"] = [str(clean_html(el).prettify()) for el in content_elements]

        data_wrapper = soup.select_one("div.info-data3")
        if not data_wrapper:
            return None

        for dl in data_wrapper.select("dl"):
            dt = dl.select_one("dt")
            dd = dl.select_one("dd")

            if not dt or not dd:
                continue

            category = dt.get_text(strip=True)
            content = dd.get_text(strip=True)

            if category == "대상":
                dto_dict["target"] = content

            elif category == "상환방법":
                dto_dict["repayment_method"] = content

            elif category == "기간":
                dto_dict["period"] = content

            elif category == "최고":
                dto_dict["credit_limit"] = content

        dto = LoanDTO.model_validate(dto_dict)

        return dto


def parse_loan_code(input: str) -> str | None:
    _match = re.search(r"dtlLoan\('([^']+)'", input)
    code = _match.group(1) if _match else None

    return code
