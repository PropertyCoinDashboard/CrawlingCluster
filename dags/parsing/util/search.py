import asyncio
from collections import deque


import aiohttp
from aiohttp.client_exceptions import ClientConnectorError
from bs4 import BeautifulSoup
from parsing.util.data_structure import indstrict
from parsing.util.parser_util import url_addition
from parsing.util._typing import (
    UrlDataStructure,
    OuterData,
    ProcessUrlCollect,
    UrlCollect,
)


# DFS 함수 정의
def recursive_dfs(
    node: int, graph: UrlDataStructure, discovered: list = None
) -> list[int]:
    if discovered is None:
        discovered = []

    discovered.append(node)
    for n in graph.get(node, []):
        if n not in discovered:
            recursive_dfs(n, graph, discovered)

    return discovered


# BFS 함수 정의
def iterative_bfs(start_v: int, graph: dict[int, list[str]]) -> UrlCollect:
    start = deque()

    visited = set()
    queue = deque([start_v])
    visited.add(start_v)
    while queue:
        node: int = queue.popleft()
        if graph.get(node, []):
            start.append(graph[node])
            if node not in visited:
                visited.add(node)
                queue.append(node)

    return start


def deep_dive_search(page: ProcessUrlCollect, objection: str) -> UrlCollect:
    """
    Args:
        page (ProcessUrlCollect): 크롤링하려는 프로세스
        objection (str): 어떤 페이지에 할것인지

    Returns:
        UrlCollect: deque([URL 뭉치들]) [starting]
    """
    starting_queue = deque()
    tree: UrlDataStructure = indstrict(page)
    dfs: list[int] = recursive_dfs(1, tree)

    print(f"{objection}의 검색된 노드의 순서 --> {dfs}")
    for location in dfs:
        try:
            element: OuterData = tree[location]
            for num in element.keys():
                urls: list[str] = iterative_bfs(num, element).pop()
                starting_queue.append(urls)
        except (KeyError, IndexError):
            continue
    return starting_queue


class AsyncRequestAcquisitionHTML:
    def __init__(
        self,
        session: aiohttp.ClientSession,
        url: str,
        params: dict[str, str] | None = None,
        headers: dict[str, str] | None = None,
    ) -> None:
        """비동기 세션

        Args:
            session (aiohttp.ClientSession): 비동기 세션
            url (str): 타겟 URL
            params (dict[str, str] | None, optional): 파라미터. 기본은 None.
            headers (dict[str, str] | None, optional): 헤더. 기본은 None.
        """
        self.url = url
        self.params = params
        self.headers = headers
        self.session = session

    @staticmethod
    async def asnyc_request(url: str) -> str | dict[str, int]:
        """request 요청 200 분류

        Args:
            url (str): 타겟 URL

        Returns:
            tuple[str, int]: (url, status_code)
        """
        async with aiohttp.ClientSession() as session:
            return await AsyncRequestAcquisitionHTML(
                session, url
            ).asnyc_status_classifer()

    @staticmethod
    async def async_html(
        type_: str,
        url: str,
        params: dict[str, str] | None = None,
        headers: dict[str, str] | None = None,
    ) -> str | dict:
        """html or json

        Args:
            type_ (str): 타입 (HTML, JSON)
            url (str): 타겟 URL
            params (dict[str, str] | None, optional): 파라미터. 기본은 None.
            headers (dict[str, str] | None, optional): 헤더. 기본은 None.

        Returns:
            _type_: 각 형태에 맞춰서 리턴 HTML(str) or JSON
        """
        async with aiohttp.ClientSession() as session:
            try:
                return await AsyncRequestAcquisitionHTML(
                    session, url, params, headers
                ).async_source(type_)
            except ClientConnectorError:
                return None

    async def async_source(self, type_: str) -> str | dict:
        """위에 쓰고 있는 함수 본체"""
        async with self.session.get(
            url=self.url, params=self.params, headers=self.headers
        ) as response:
            match type_:
                case "html":
                    return await response.text()
                case "json":
                    return await response.json()

    async def asnyc_status_classifer(self) -> str | dict[str, int]:
        """위에 쓰고 있는 함수 본체"""
        async with self.session.get(
            url=self.url, params=self.params, headers=self.headers
        ) as response:
            match response.status:
                case 200:
                    return self.url
                case _:
                    return {"status": response.status}


class AsyncWebCrawler:
    def __init__(self, start_url: str, max_pages: int, max_depth: int) -> None:
        self.start_url = start_url
        self.max_pages = max_pages
        self.max_depth = max_depth
        self.visited_urls = set()
        self.url_queue = asyncio.Queue()
        self.url_queue.put_nowait((start_url, 0))  # Put start URL with depth 0
        self.results = {}

    def parse_links(self, content: str, base_url: str) -> set[str]:
        soup = BeautifulSoup(content, "lxml")
        links = set()
        for a_tag in soup.find_all("a", href=True):
            link: str = a_tag["href"]
            if link.startswith("/"):
                link = url_addition(base_url, link)
            if link.startswith("http"):
                links.add(link)
        return links

    async def crawl(self) -> None:
        while not self.url_queue.empty() and len(self.visited_urls) < self.max_pages:
            current_url, depth = await self.url_queue.get()

            if current_url in self.visited_urls or depth > self.max_depth:
                continue

            self.visited_urls.add(current_url)
            content = await AsyncRequestAcquisitionHTML.async_html("html", current_url)

            if content:
                if depth < self.max_depth:
                    new_links = self.parse_links(content, current_url)
                    self.results[current_url] = new_links
                    for link in new_links:
                        if link not in self.visited_urls:
                            await self.url_queue.put((link, depth + 1))

    async def run(self, num_tasks: int = 4) -> dict[str, set[str]]:
        tasks = [asyncio.create_task(self.crawl()) for _ in range(num_tasks)]
        await asyncio.gather(*tasks)
        return self.results
