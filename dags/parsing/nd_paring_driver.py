import aiohttp
from bs4 import BeautifulSoup

from parsing.config.properties import naver_id, naver_secret, naver_url
from parsing.util.util_parser import (
    AsyncRequestAcquisitionHTML as ARAH,
    soup_data,
    href_from_a_tag,
)


class DaumNewsParsingDriver:
    def __init__(self, d_header, earch_query, total_pages):
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
