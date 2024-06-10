from abc import ABC, abstractmethod

import configparser
from pathlib import Path
from collections import deque


from parsing.util._typing import UrlDictCollect
from parsing.util.parser_util import time_extract
from parsing.util.search import AsyncRequestAcquisitionHTML as ARAH


# 부모 경로
path_location = Path(__file__)
# key_parser
parser = configparser.ConfigParser()
parser.read(f"{path_location.parent.parent}/config/url.conf")

naver_id: str = parser.get("naver", "X-Naver-Client-Id")
naver_secret: str = parser.get("naver", "X-Naver-Client-Secret")
naver_url: str = parser.get("naver", "NAVER_URL")


class NaverNewsParsingDriver:
    """네이버 비동기 API 호출"""

    def __init__(self, target: str, count: int) -> None:
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
            f"{naver_url}/news.json?query={self.target}&start={self.count}&display=100"
        )

    async def fetch_page_urls(self) -> dict:
        """JSON 비동기 호출
        Args:
            url (str): URL
            headers (dict[str, str]): 해더
        Returns:
            dict: JSON
        """
        try:
            urls = await ARAH.async_html(
                type_="json",
                url=self.url,
                headers=self.header,
            )
            return (urls, True)
        except ConnectionError:
            return False

    async def extract_news_urls(self) -> UrlDictCollect:
        """new parsing
        Args:
            items (str): 첫번째 접근
            link (str): url
        Returns:
            UrlCollect: [URL, ~]
        """
        print("Naver 시작합니다")
        res_data: dict = await self.fetch_page_urls()
        data: list[dict[str]] = list(
            map(
                lambda item: {
                    "title": item["title"],
                    "link": item["originallink"],
                    "date": time_extract(item["pubDate"]),
                },
                res_data[0]["items"],
            )
        )
        urls = deque(data)

        return urls
