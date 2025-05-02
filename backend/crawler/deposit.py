"""예금상품 크롤러"""

import re
from typing import Dict, List, Optional

from pgvector import SparseVector
from selenium.webdriver.common.by import By

from crawler.base import BASE_URL, SeleniumClient, BaseKBCrawler

import time

import requests

from bs4 import BeautifulSoup

from db.common import V_DIM
from db.models.deposit import DepositModel, DepositChunkModel
from preprocess.html import clean_html

from pydantic import BaseModel

from utils.embed import create_embedding


class DepositDTO(BaseModel):
    url: str

    title: str
    contents: List[str]
    description: str

    category: Optional[str] = None

    period: Optional[str] = None   # 기간
    amount: Optional[str] = None   # 금액
    interest: Optional[str] = None # 금리


class DepositCrawler(BaseKBCrawler[DepositDTO, DepositModel], SeleniumClient):

    def scrape_urls_dict(self, page_code: str):

        result: Dict[str, List[str]] = {}

        print(f"[{page_code}] 예금 상품 목록 불러오는중...")

        url = f"https://obank.kbstar.com/quics?page={page_code}#CP"

        self.driver.get(url)

        time.sleep(10)
        
        anchor_selector = "#tabMenutabMain > li > a"
        anchors = self.driver.find_elements(by=By.CSS_SELECTOR, value=anchor_selector)

        url_factory = "{}/quics?page={}&cc=b061496:b061645&isNew=N&prcode={}&QSL=F"

        for idx in range(len(anchors)):
            anchors = self.driver.find_elements(by=By.CSS_SELECTOR, value=anchor_selector)
            anchor = anchors[idx]

            category = anchor.text

            anchor.click()

            time.sleep(10)

            curr_codes: List[str] = []

            for element in self.pagination_generator():
                element.click()

                time.sleep(10)

                selector = "ul.list-product1 > li > div.area1 > a"
                deposits = self.driver.find_elements(by=By.CSS_SELECTOR, value=selector)
                onclicks = [deposit.get_attribute("onclick") for deposit in deposits]
                onclicks = [onclick for onclick in onclicks if onclick is not None]
                codes = [parse_deposit_code(onclick) for onclick in onclicks]
                codes = [code for code in codes if code is not None]

                curr_codes += codes

            curr_urls = [url_factory.format(BASE_URL, page_code, code) for code in curr_codes]
            result[category] = curr_urls

        return result

    def scrape_urls(self, page_code):

        print(f"[{page_code}] 예금 상품 목록 불러오는중...")

        url = f"https://obank.kbstar.com/quics?page={page_code}"

        self.driver.get(url)

        time.sleep(0.1)

        uls = self.driver.find_elements(by=By.CSS_SELECTOR, value="#tabMenutabMain")

        tot_codes: List[str] = []

        for ul in uls:
            ul.click()
            time.sleep(10)

            for element in self.pagination_generator():
                element.click()

                time.sleep(5)

                selector = "ul.list-product1 > li > div.area1 > a"
                deposits = self.driver.find_elements(by=By.CSS_SELECTOR, value=selector)
                onclicks = [deposit.get_attribute("onclick") for deposit in deposits]
                onclicks = [onclick for onclick in onclicks if onclick is not None]
                codes = [parse_deposit_code(onclick) for onclick in onclicks]
                codes = [code for code in codes if code is not None]

                tot_codes += codes

        url_factory = "{}/quics?page={}&cc=b061496:b061645&isNew=N&prcode={}&QSL=F"
        urls = [url_factory.format(BASE_URL, page_code, code) for code in tot_codes]

        return urls

    def dto2orm(self, dto):

        if not dto.category:
            raise ValueError("`DepositDTO` must be include `category` property")

        orm = DepositModel()

        orm.url = dto.url
        orm.title = dto.title
        orm.category = dto.category
        orm.description = dto.description

        basic_info = (
            f"기간: {dto.period if dto.period else "NONE"}\n"
            f"금액: {dto.amount if dto.amount else "NONE"}\n"
            f"금리: {dto.interest if dto.interest else "NONE"}\n"
            "---\n"
        )

        for idx, content in enumerate(dto.contents):
            dto.contents[idx] = basic_info + content

        if dto.period:
            orm.period = dto.period

        if dto.amount:
            orm.amount = dto.amount

        if dto.interest:
            orm.interest = dto.interest

        print("임베딩 하는중 ...")
        embeddings = create_embedding(dto.contents, html=True, chunking=False)

        chunks = [
            DepositChunkModel(
                content=content,
                dense_vector=emb.dense,
                sparse_vector=SparseVector(emb.sparse, V_DIM),
            ) for content, emb in zip(dto.contents, embeddings)
        ]

        orm.chunks = chunks

        return orm

    def scrape_detail(self, url):
        print(f"예금 상품 크롤링 하는중... ({url})")

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

            if category == "기간":
                dto_dict["period"] = content

            elif category == "금액":
                dto_dict["amount"] = content

            elif category == "금리":
                dto_dict["interest"] = content

        dto = DepositDTO.model_validate(dto_dict)

        return dto


def parse_deposit_code(input: str) -> str | None:
    _match = re.search(r"dtlDeposit\('([^']+)'", input)
    code = _match.group(1) if _match else None

    return code
