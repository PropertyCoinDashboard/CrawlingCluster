"""
crawling selenium 
"""

import configparser
from pathlib import Path
from typing import Any, Coroutine
from abc import ABCMeta, abstractmethod


import aiohttp
import requests
from parsing.schema.create_log import log


# 부모 경로
path_location = Path(__file__).parent.parent

# key_parser
parser = configparser.ConfigParser()
parser.read(f"{path_location}/config/url.conf")

naver_id: str = parser.get("naver", "X-Naver-Client-Id")
naver_secret: str = parser.get("naver", "X-Naver-Client-Secret")
naver_url: str = parser.get("naver", "NAVER_URL")

daum_auth: str = parser.get("daum", "Authorization")
daum_url: str = parser.get("daum", "DAUM_URL")


class NewsParsingDrive(metaclass=ABCMeta):
    """
    유틸리티
    """

    def __init__(self, count: int, data: str, site: str) -> None:
        """
        Args:
            count        (int): 크롤링할 데이터의 카운트
            data         (str): 크롤링할 데이터
            site         (str): 크롤링 호출 사이트
        """
        self.count = count
        self.data = data
        self.logger = log(f"{site}", f"{path_location}/log/info.log")

    @abstractmethod
    def get_build_header(self) -> dict[str, str]:
        """parsing authentication header key

        Returns:
            dict[str, Any]: header key
        """
        return NotImplementedError()

    @abstractmethod
    def get_build_url(self) -> str:
        """api site url

        Args:
            url (str): url

        Returns:
            str: url
        """
        return NotImplementedError()

    async def url_parsing(
        self, url: str, headers: dict[str, Any]
    ) -> Coroutine[Any, Any, Any]:
        """
        url parsing
        """
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=headers) as resp:
                match resp.status:
                    case 200:
                        return await resp.json()
                    case _:
                        raise requests.exceptions.RequestException(
                            f"API Request에 실패하였습니다 status code --> {resp.status}"
                        )

    async def get_news_data(
        self, target: str, items: str, titles: str, link: str
    ) -> Coroutine[Any, Any, None]:
        """new parsing

        Args:
            target (str): 타겟 API
            items (str): 첫번째 접근
            title (str): 타이틀
            link (str): url

        Returns:
            _type_: str
        """
        res_data = await self.url_parsing(self.get_build_url(), self.get_build_header())

        count = 0
        for item in res_data[items]:
            title = item[titles]
            url = item[link]
            count += 1

            print(f"{target} Title: {title}")
            print(f"{target} URL: {url}")
            print("--------------------")
        self.logger.info("%s parsing data --> %s", target, count)


class NaverNewsParsingDriver(NewsParsingDrive):
    """네이버 API 호출

    Args:
        SeleniumUtility (_type_): 유틸리티 클래스
    """

    def __init__(self, count: int, data: str) -> None:
        """
        Args:
            count (int, optional): 뉴스 크롤링할 사이트 1 ~ 몇개 까지 가져올까 .
            data  (str, optional): 뉴스 크롤링할 사이트 데이터 검색.
        Function:
            naver_news_data
                - 파라미터 존재하지 않음
                - return 값 None
                    - items(dict, if NotFound is optional) :
                        - items 안에 list가 있음 각 self.data 의 내용의 뉴스가 담겨 있음
                            - link -> href
                            - title(str, optional) title 존재 안할 수 있음
        """
        super().__init__(count, data, site="Naver")

    def get_build_header(self) -> dict[str, str]:
        return {
            "X-Naver-Client-Id": naver_id,
            "X-Naver-Client-Secret": naver_secret,
        }

    def get_build_url(self) -> str:
        return f"{naver_url}/news.json?query={self.data}&start=1&display={self.count}"

    async def get_naver_news_data(self) -> None:
        """
        naver news parsing
        """
        await self.get_news_data(
            target="Naver", items="items", titles="title", link="link"
        )


class DaumNewsParsingDriver(NewsParsingDrive):
    """다음 API 호출

    Args:
        SeleniumUtility (_type_): 유틸리티 클래스
    """

    def __init__(self, count: int, data: str) -> None:
        """
        Args:
            count (int, optional): 뉴스 크롤링할 사이트 1 ~ 몇개 까지 가져올까 .
            data (str, optional): 뉴스 크롤링할 사이트 데이터 검색.
        Function:
            get_daum_news_data
                - 파라미터 존재하지 않음
                - return 값 None
                    - documents(dict, if NotFound is optional) :
                        - documents 안에 list가 있음 각 self.data 의 내용의 뉴스
                            - url -> href
                            - title(str, optional) title 존재 안할 수 있음
        """
        super().__init__(count, data, site="Daum")

    def get_build_header(self) -> dict[str, str]:
        return {"Authorization": daum_auth}

    def get_build_url(self) -> str:
        return (
            f"{daum_url}/web?sort=accuracy&page=1&size={self.count}&query={self.data}"
        )

    async def get_daum_news_data(self) -> None:
        """
        daum news parsing
        """
        await self.get_news_data(
            target="Daum", items="documents", titles="title", link="url"
        )


class GoogleSearchDataInfomer:
    pass
