"""
crawling selenium 
"""

import configparser
from pathlib import Path
from abc import ABCMeta, abstractmethod

from parsing.util.util_parser import get_news_data


# 부모 경로
path_location = Path(__file__).parent.parent.parent

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

    def __init__(self, count: int, data: str) -> None:
        """
        Args:
            count        (int): 크롤링할 데이터의 카운트
            data         (str): 크롤링할 데이터
        """
        self.count = count
        self.data = data

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


class NaverNewsParsingDriver(NewsParsingDrive):
    """네이버 API 호출

    Args:
        SeleniumUtility (_type_): 유틸리티 클래스
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
        await get_news_data(
            target="Naver",
            items="items",
            titles="title",
            link="link",
            target_url=self.get_build_url(),
            build_header=self.get_build_header(),
        )


class DaumNewsParsingDriver(NewsParsingDrive):
    """다음 API 호출

    Args:
        SeleniumUtility (_type_): 유틸리티 클래스
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
        await get_news_data(
            target="Daum",
            items="documents",
            titles="title",
            link="url",
            target_url=self.get_build_url(),
            build_header=self.get_build_header(),
        )
