from typing import Dict, List
from bs4 import BeautifulSoup
from selenium.webdriver import Chrome
from selenium.webdriver.common.by import By

import time

from domains.common.scrapers import BaseHKCralwer
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait


class RawHKFinanceCrawler(BaseHKCralwer):
    """한국경제 금융정책 페이지 스크래퍼"""

    NEXT_PAGE_BTN_SELECTOR = "a.btn-next"

    def scrape_detail(self, url: str):
        print(f"금융 정책 상세 데이터 수집중 (url: {url})")

        self.driver.get(url)

        time.sleep(0.1)

        html = self.driver.page_source
        soup = BeautifulSoup(html)

        data: Dict[str, str | None] = {"url": url, "html": html}

        title_element = soup.select_one("h1.headline")
        content_element = soup.select_one("div.article-body")
        data["title"] = title_element.get_text(strip=True) if title_element else None

        if content_element:
            data["content"] = content_element.get_text(strip=True)
            thumbnail_element = content_element.select_one("img")
            if thumbnail_element:
                src = thumbnail_element.get("src")
                data["thumbnail"] = str(src)

        return data

    def scrape_urls(self, path: str = "/financial-market/financial-policy"):
        print("한국경제 데이터 URL 수집중...")

        list_url = f"{self.BASE_URL}{path}"
        self.driver.get(list_url)

        urls: List[str] = []

        while True:

            article_anchor_selector = 'ul.news-list h2.news-tit > a'
            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located(
                    (By.CSS_SELECTOR, article_anchor_selector)))

            articles = self.driver.find_elements(by=By.CSS_SELECTOR,
                                                 value=article_anchor_selector)

            for article in articles:
                href = article.get_attribute("href")
                if not href:
                    continue

                urls.append(href)

            if not self.has_next_page:
                break

            if self.next_page_button:
                self.next_page_button.click()
            else:
                raise ValueError("크롤링 과정에서 일시적인 오류가 발생했습니다.")

        return urls


import json

if __name__ == "__main__":

    driver = Chrome()
    crawler = RawHKFinanceCrawler(driver)

    urls = crawler.scrape_urls()

    datas = []

    with open("articles.jsonl", "w") as f:

        for url in urls:
            data = crawler.scrape_detail(url)
            json_line = json.dumps(data, ensure_ascii=False)
            f.write(json_line + "\n")

    print("크롤링 성공!")
