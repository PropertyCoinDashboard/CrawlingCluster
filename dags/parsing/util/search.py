import time
import requests
from bs4 import BeautifulSoup
import aiohttp
from collections import deque
from parsing.util.data_structure import indstrict
from parsing.util.parser_util import url_addition
from parsing.util._typing import (
    UrlDataStructure,
    ProcessUrlCollect,
    OuterData,
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


def bfs_crawl(start_url: str, max_depth=2):
    visited = set()
    queue = deque([(start_url, 0)])

    while queue:
        url, depth = queue.popleft()
        if depth > max_depth:
            break

        if url in visited:
            continue

        visited.add(url)
        print(f"Depth: {depth}, URL: {url}")

        try:
            response = requests.get(url)
            if response.status_code != 200:
                continue

            soup = BeautifulSoup(response.text, "html.parser")

            links = [a["href"] for a in soup.find_all("a", href=True)]
            time.sleep(2)
            for link in links:
                if link.startswith("/"):
                    link = url_addition(start_url)
                elif not link.startswith("http" or "https"):
                    continue  # 다른 프로토콜이나 상대 경로가 아닌 링크는 무시

                if link not in visited:
                    queue.append((link, depth + 1))

        except Exception as e:
            print(f"URL 변환 X {url}: {e}")


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
        UrlCollect: deque([URL 뭉치들]) [startingßå]
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
    async def asnyc_request(url: str) -> tuple[str, int]:
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
            return await AsyncRequestAcquisitionHTML(
                session, url, params, headers
            ).async_source(type_)

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
                    return {self.url: response.status}
