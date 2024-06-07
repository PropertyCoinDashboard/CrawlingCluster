from abc import ABC, abstractmethod

import configparser
from pathlib import Path
import time
import asyncio
from collections import deque

from bs4 import BeautifulSoup

from parsing.util._typing import UrlCollect, UrlDictCollect
from parsing.util.parser_util import soup_data, href_from_a_tag, time_extract
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

        # time.sleep(3)
        url = deque(url)
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
        self.url = f"{naver_url}/news.json?query={self.target}&start=1&display={self.count*10}sort=date"

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

    async def extract_news_urls(self) -> UrlDictCollect:
        """new parsing
        Args:
            items (str): 첫번째 접근
            link (str): url
        Returns:
            UrlCollect: [URL, ~]
        """
        print("Naver 시작합니다")
        res_data: dict = await self.fetch_page_urls(url=self.url, headers=self.header)
        data: list[dict[str, str, str]] = list(
            map(
                lambda item: {
                    "title": item["title"],
                    "link": item["originallink"],
                    "date": time_extract(item["pubDate"]),
                },
                res_data["items"],
            )
        )
        urls = deque(data)

        return urls
