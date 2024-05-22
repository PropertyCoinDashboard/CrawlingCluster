import aiohttp
from collections import deque
from parsing.util.data_structure import indstrict
from parsing.util._typing import (
    UrlDataStructure,
    ProcessUrlCollect,
    UrlCollect,
    OuterData,
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
        self.url = url
        self.params = params
        self.headers = headers
        self.session = session

    @staticmethod
    async def asnyc_request(url: str):
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
    ):
        async with aiohttp.ClientSession() as session:
            return await AsyncRequestAcquisitionHTML(
                session, url, params, headers
            ).async_source(type_)

    async def async_source(self, type_: str) -> str:
        async with self.session.get(
            url=self.url, params=self.params, headers=self.headers
        ) as response:
            match type_:
                case "html":
                    return await response.text()
                case "json":
                    return await response.json()

    async def asnyc_status_classifer(self) -> tuple[str, int]:
        async with self.session.get(
            url=self.url, params=self.params, headers=self.headers
        ) as response:
            match response.status:
                case 200:
                    return self.url
                case _:
                    return {self.url: response.status}
