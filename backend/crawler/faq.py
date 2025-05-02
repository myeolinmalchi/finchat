"""FAQ 크롤러"""

from typing import List, Optional
from bs4 import BeautifulSoup
from pgvector import SparseVector
from pydantic import BaseModel
import requests
from selenium.webdriver.common.by import By

import time

from crawler.base import SeleniumClient, BaseKBCrawler
from db.common import V_DIM
from db.models.faq import FaqModel
from preprocess.html import clean_html
from utils.embed import create_embedding


class FaqDTO(BaseModel):

    url: str
    title: str
    content: str
    category: Optional[str] = None


class FaqCrawler(BaseKBCrawler[FaqDTO, FaqModel], SeleniumClient):

    def scrape_urls(self, page_code: str):

        print(f"[{page_code}] FAQ 목록 불러오는중...")

        url = self.get_page_url(page_code)

        self.driver.get(url)

        time.sleep(10)

        tot_urls: List[str] = []

        for element in self.pagination_generator():
            element.click()

            time.sleep(0.2)

            selector = "table > tbody > tr > td.left > a"
            items = self.driver.find_elements(by=By.CSS_SELECTOR, value=selector)

            paths = [item.get_attribute("href") for item in items]
            urls = [path for path in paths if path is not None]

            tot_urls += urls
        return tot_urls

    def scrape_detail(self, url):

        print(f"FAQ 크롤링 하는중... ({url})")

        res = requests.get(url)
        res.raise_for_status()

        dto_dict = {}

        soup = BeautifulSoup(res.text)

        title_element = soup.select_one("dl.faq_view.board_view > dt > strong")
        content_element = soup.select_one("#view_cont")

        if not title_element or not content_element:
            return None

        dto_dict["url"] = url
        dto_dict["title"] = title_element.get_text("", strip=True)
        dto_dict["content"] = str(clean_html(content_element).prettify())

        dto = FaqDTO.model_validate(dto_dict)

        return dto

    def dto2orm(self, dto):

        if not dto.category:
            raise ValueError("`FaqDTO` must be include `category` property")

        orm = FaqModel()

        orm.url = dto.url
        orm.title = dto.title
        orm.content = dto.content
        orm.category = dto.category

        print("임베딩 하는중 ...")

        title_embeddings, content_embeddings = create_embedding([dto.title, dto.content], html=True, chunking=False)

        orm.title_dense_vector = title_embeddings.dense
        orm.title_sparse_vector = SparseVector(title_embeddings.sparse, V_DIM)

        orm.content_dense_vector = content_embeddings.dense
        orm.content_sparse_vector = SparseVector(content_embeddings.sparse, V_DIM)

        return orm
