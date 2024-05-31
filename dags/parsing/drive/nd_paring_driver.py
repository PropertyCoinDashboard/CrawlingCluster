from abc import ABC, abstractmethod

import os
import configparser
from pathlib import Path
import time
import asyncio
from collections import deque

from bs4 import BeautifulSoup

from parsing.util._typing import UrlCollect
from parsing.util.parser_util import soup_data, href_from_a_tag
from parsing.util.search import AsyncRequestAcquisitionHTML as ARAH


# 부모 경로
path_location = Path(__file__)
# key_parser
parser = configparser.ConfigParser()
parser.read(f"{path_location.parent.parent}/config/url.conf")

naver_id: str = parser.get("naver", "X-Naver-Client-Id")
naver_secret: str = parser.get("naver", "X-Naver-Client-Secret")
naver_url: str = parser.get("naver", "NAVER_URL")


class AbstractAsyncNewsParsingDriver(ABC):
    """비동기 API 호출 추상화"""

    def __init__(self, target: str, count: int) -> None:
        self.target = target
        self.count = count

    @abstractmethod
    async def fetch_page_urls(self, url: str) -> str:
        raise NotImplementedError()

    @abstractmethod
    async def extract_news_urls(self) -> deque:
        raise NotImplementedError()


class GoogleNewsParsingDriver(AbstractAsyncNewsParsingDriver):
    """구글 크롤링"""

    def __init__(self, target: str, count: int) -> None:
        super().__init__(target, count)
        self.url = "https://www.google.com/search"
        self.count = count * 10
        self.params = {
            "q": "BTC",
            "tbm": "nws",
            "gl": "ko",
            "hl": "kr",
            "num": 10,
        }

    async def fetch_page_urls(self, url: str, page: int) -> str:
        """html 비동기 호출
        Args:
            url (str): URL
            page (int): 페이지 긁어올곳

        Returns:
            str: HTML
        """
        self.params["start"] = page
        urls = await ARAH.async_html(
            type_="html",
            url=url,
            params=self.params,
        )
        return urls

    async def get_google_news_urls(self) -> list[str]:
        """
        Returns:
            list[str]: [url 를 담고 있는 a 요소들]
        """
        print("google 시작합니다")
        tasks: list[str] = [
            self.fetch_page_urls(self.url, page) for page in range(0, self.count, 10)
        ]

        all_urls = await asyncio.gather(*tasks)
        return all_urls

    async def extract_news_urls(self) -> UrlCollect:
        """URL 모음집
        Returns:
            UrlCollect: [URL, ~]
        """
        url = []
        htmls: list[str] = await self.get_google_news_urls()
        for html in htmls:
            html_data: list = soup_data(
                html_data=html,
                element="div",
                elements={"class": "Gx5Zad fP1Qef xpd EtOod pkphOe"},
                soup=BeautifulSoup(html, "lxml"),
            )
            for data in html_data:
                for a_tag in data.find_all("a"):
                    url.append(a_tag["href"].split("?q=")[1].split("&sa")[0])

        return url
        # time.sleep(3)
        # url = deque(list(map(href_from_a_tag, a_tag_list)) for a_tag_list in html_data)


class DaumNewsParsingDriver(AbstractAsyncNewsParsingDriver):
    """다음 크롤링"""

    def __init__(self, target: str, count: int, d_header: dict[str, str]) -> None:
        super().__init__(target, count)
        self.d_header = d_header
        self.url = "https://search.daum.net/search"
        self.params: dict[str, str] = {
            "nil_suggest": "btn",
            "w": "news",
            "DA": "STC",
            "cluster": "y",
            "q": self.target,
            "sort": "accuracy",
        }

    async def fetch_page_urls(
        self, url: str, headers: dict[str, str], page: int
    ) -> str:
        """html 비동기 호출
        Args:
            url (str): URL
            headers (dict[str, str]): 해더
            page (int): 페이지 긁어올곳

        Returns:
            str: HTML
        """
        self.params["p"] = page
        urls = await ARAH.async_html(
            type_="html",
            url=url,
            params=self.params,
            headers=headers,
        )
        return urls

    async def get_daum_news_urls(self) -> list[str]:
        """
        Returns:
            list[str]: [url 를 담고 있는 a 요소들]
        """
        print("Daum 시작합니다")
        tasks: list[str] = [
            self.fetch_page_urls(self.url, self.d_header, page)
            for page in range(1, self.count + 1)
        ]

        all_urls = await asyncio.gather(*tasks)
        return all_urls

    async def extract_news_urls(self) -> UrlCollect:
        """URL 모음집
        Returns:
            UrlCollect: [URL, ~]
        """
        htmls: list[str] = await self.get_daum_news_urls()
        html_data: list[list[str]] = [
            soup_data(
                html_data=html,
                element="a",
                elements={"class": "tit_main fn_tit_u"},
                soup=BeautifulSoup(html, "lxml"),
            )
            for html in htmls
        ]
        time.sleep(3)
        url = deque(list(map(href_from_a_tag, a_tag_list)) for a_tag_list in html_data)
        return url


class NaverNewsParsingDriver(AbstractAsyncNewsParsingDriver):
    """네이버 비동기 API 호출"""

    def __init__(self, target: str, count: int) -> None:
        super().__init__(target, count)
        """
        Args:
            target (str): 긁어올 타겟
            count (int): 횟수
        """
        self.target = target
        self.count = count
        self.header = {
            "X-Naver-Client-Id": naver_id,
            "X-Naver-Client-Secret": naver_secret,
        }
        self.url = (
            f"{naver_url}/news.json?query={self.target}&start=1&display={self.count*10}"
        )

    async def fetch_page_urls(self, url: str, headers: dict[str, str]) -> dict:
        """JSON 비동기 호출
        Args:
            url (str): URL
            headers (dict[str, str]): 해더
        Returns:
            dict: JSON
        """
        urls = await ARAH.async_html(
            type_="json",
            url=url,
            headers=headers,
        )
        return urls

    async def extract_news_urls(self) -> UrlCollect:
        """new parsing
        Args:
            items (str): 첫번째 접근
            link (str): url
        Returns:
            UrlCollect: [URL, ~]
        """
        print("Naver 시작합니다")
        res_data: dict = await self.fetch_page_urls(url=self.url, headers=self.header)

        url: list[str] = [item["link"] for item in res_data["items"]]
        urls: UrlCollect = deque(
            list(url[count : count + 10] for count in range(0, len(url), self.count))
        )
        return urls
