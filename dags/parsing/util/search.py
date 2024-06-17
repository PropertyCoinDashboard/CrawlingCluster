import re
import asyncio
import aiohttp
from datetime import datetime
from bs4 import BeautifulSoup
from parsing.util.parser_util import url_addition


class AsyncRequestAcquisitionHTML:
    def __init__(
        self,
        session: aiohttp.ClientSession,
        url: str,
        params: dict[str, str] | None = None,
        headers: dict[str, str] | None = None,
    ) -> None:
        self.url = url
        self.params = params
        self.headers = headers
        self.session = session

    async def async_source(
        self, response: aiohttp.ClientResponse, response_type: str
    ) -> str | dict:
        """비동기 방식으로 원격 자원에서 HTML 또는 JSON 데이터를 가져옴

        Args:
            response (aiohttp.ClientResponse) : session
            response_type (str): 가져올 데이터의 유형 ("html" 또는 "json")

        Returns:
            str | dict: HTML 또는 JSON 데이터
        """
        try:
            match response_type:
                case "html":
                    return await response.text("utf-8")
                case "json":
                    return await response.json()
        except UnicodeDecodeError:
            pass

    async def async_request(
        self, response: aiohttp.ClientResponse
    ) -> str | dict[str, int] | dict[str, str]:
        """비동기 방식으로 원격 자원에 요청하고 상태 코드를 분류함

        Args:
            response (aiohttp.ClientResponse) : session

        Returns:
            str | dict[str, int | str]: 요청 결과 URL 또는 상태 코드
        """
        match response.status:
            case 200:
                return self.url
            case _:
                return {"status": response.status}

    async def async_type(
        self, type_: str, source: str = None
    ) -> str | dict | dict[str, int] | dict[str, str] | None:
        async with self.session.get(
            url=self.url, params=self.params, headers=self.headers
        ) as response:
            match type_:
                case "source":
                    return await self.async_source(response, source)
                case "request":
                    return await self.async_request(response)

    # fmt: off
    @staticmethod
    async def async_request_status(url: str) -> str | dict[str, int] | dict[str, str]:
        """주어진 URL에 대해 비동기 방식으로 요청하고 상태 코드를 반환함

        Args:
            url (str): 요청할 URL

        Returns:
            str | dict[str, int] | dict[str, str] : 요청 결과 URL 또는 상태 코드
        """
        timeout = aiohttp.ClientTimeout(total=10)  # 10초의 시간 제한 설정
        async with aiohttp.ClientSession(timeout=timeout) as session:
            return await AsyncRequestAcquisitionHTML(session, url).async_type(type_="request")

    @staticmethod
    async def async_fetch_content(
        response_type: str,
        url: str,
        params: dict[str, str] | None = None,
        headers: dict[str, str] | None = None,
    ) -> str | dict:
        """비동기 방식으로 원격 자원에서 HTML 또는 JSON 데이터를 가져옴

        Args:
            response_type (str): 가져올 데이터의 유형 ("html" 또는 "json")
            url (str): 가져올 데이터의 URL
            params (dict[str, str] | None, optional): 요청 시 사용할 파라미터
            headers (dict[str, str] | None, optional): 요청 시 사용할 헤더

        Returns:
            str | dict: HTML 또는 JSON 데이터
        """
        timeout = aiohttp.ClientTimeout(total=10)  # 10초의 시간 제한 설정
        async with aiohttp.ClientSession(timeout=timeout) as session:
            return await AsyncRequestAcquisitionHTML(
                    session, url, params, headers
                ).async_type(type_="source", source=response_type)


class AsyncWebCrawler:
    def __init__(self, start_url: str, max_pages: int, max_depth: int) -> None:
        self.start_url = start_url
        self.max_pages = max_pages
        self.max_depth = max_depth
        self.visited_urls = set()
        self.url_queue = asyncio.Queue()
        self.url_queue.put_nowait((start_url, 0))  # Put start URL with depth 0
        self.results = {}

    # fmt: off
    def parse_links(self, content: str, base_url: str) -> tuple[set, list[dict[str, str]]]:
        soup = BeautifulSoup(content, "lxml")
        links = set()
        data_list: list[dict[str, str]] = []

        for a_tag in soup.find_all("a", href=True):
            link: str = a_tag["href"]
            # 자바스크립트 링크 제외
            if link.startswith(("javascript:", "#", "-", "i")) or "index.html" in link:
                continue

            if link.startswith("/"):
                link = url_addition(base_url, link)
            if link.startswith("http"):
                links.add(link)

            # 링크 정보를 데이터 포맷에 추가
            data_format = {
                "title": a_tag.text,
                "link": link,
                "date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            }
            data_list.append(data_format)
        return links, data_list

    async def crawl(self) -> None:
        while not self.url_queue.empty() and len(self.visited_urls) < self.max_pages:
            current_url, depth = await self.url_queue.get()

            if current_url in self.visited_urls or depth > self.max_depth:
                continue

            self.visited_urls.add(current_url)
            content = await AsyncRequestAcquisitionHTML.async_fetch_content(
                "html", current_url
            )

            if content:
                if depth < self.max_depth:
                    new_links, url_format = self.parse_links(content, current_url)
                    self.results[current_url] = url_format
                    for link in new_links:
                        if link not in self.visited_urls:
                            await self.url_queue.put((link, depth + 1))

    async def run(self, num_tasks: int = 4) -> dict[str, set[str]]:
        tasks = [asyncio.create_task(self.crawl()) for _ in range(num_tasks)]
        await asyncio.gather(*tasks)
        return self.results
