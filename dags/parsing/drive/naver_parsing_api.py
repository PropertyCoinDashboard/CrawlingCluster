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
        self.url = f"{naver_url}/news.json?query={self.target}&start={self.count}&display=100sort=date"

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
