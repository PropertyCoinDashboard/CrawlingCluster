import aiohttp

import configparser
from pathlib import Path

from parsing.util.util_parser import (
    AsyncRequestAcquisitionHTML as ARAH,
    soup_data,
    href_from_a_tag,
)
from bs4 import BeautifulSoup


# 부모 경로
path_location = Path(__file__)

# key_parser
parser = configparser.ConfigParser()
parser.read(f"{path_location.parent}/config/url.conf")

naver_id: str = parser.get("naver", "X-Naver-Client-Id")
naver_secret: str = parser.get("naver", "X-Naver-Client-Secret")
naver_url: str = parser.get("naver", "NAVER_URL")


class DaumNewsParsingDriver:
    def __init__(
        self, n_client_id, n_client_secret, d_header, earch_query, total_pages
    ):
        self.n_client_id = n_client_id
        self.n_client_secret = n_client_secret
        self.d_header = d_header
        self.earch_query: str = earch_query
        self.total_pages: int = total_pages
        self.url = "https://search.daum.net/search"
        self.params: dict[str, str] = {
            "nil_suggest": "btn",
            "w": "news",
            "DA": "STC",
            "cluster": "y",
            "q": self.earch_query,
            "sort": "accuracy",
        }

    async def get_daum_news_urls(self) -> list[str]:
        """
        Daum 검색 엔진을 사용하여 뉴스 URL 목록을 가져옵니다.

        Args:
             search_query (str): 검색어
             total_pages (int, optional): 검색할 총 페이지 수. 기본값은 11.

        Returns:
             List[str]: 뉴스 URL 목록
        """

        all_urls = []
        async with aiohttp.ClientSession() as session:
            for page in range(1, self.total_pages + 1):
                self.params["p"] = page
                urls = await ARAH(
                    session=session,
                    url=self.url,
                    params=self.params,
                    headers=self.d_header,
                ).async_html_source()
                all_urls.append(urls)
            return all_urls

    async def extract_news_urls(self) -> list[str]:
        """
        HTML에서 뉴스 URL을 추출합니다.

        Args:
             html (str): HTML 문자열

        Returns:
             List[str]: 뉴스 URL 목록
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
        url = [list(map(href_from_a_tag, a_tag_list)) for a_tag_list in html_data]
        return url


class NaverNewsParsingDriver:
    """네이버 API 호출"""

    def __init__(self, count: int, data: str) -> None:
        self.count = count
        self.data = data

    def get_build_header(self) -> dict[str, str]:
        return {
            "X-Naver-Client-Id": naver_id,
            "X-Naver-Client-Secret": naver_secret,
        }

    def get_build_url(self) -> str:
        return f"{naver_url}/news.json?query={self.data}&start=1&display={self.count}"
