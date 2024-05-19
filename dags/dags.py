"""
기능 테스트
Airflow 발전시키기
"""

import aiohttp
from aiohttp.client_exceptions import ClientConnectionError

import asyncio
import tracemalloc
from typing import Callable, Any, Coroutine
from collections import deque
from parsing.util.util_parser import data_structure
from concurrent.futures import ThreadPoolExecutor, as_completed
from parsing.selenium_parsing import (
    GoogleMovingElementsLocation,
    BingMovingElementLocation,
)


tracemalloc.start()
ready_queue = deque()
scheduler_queue = deque()
not_request_queue = deque()


# 머금고 있어야함
def indstrict(
    page: Callable[[str, int], deque[list[str]]], target: str, counting: int
) -> dict[int, dict[int, list[str]]]:
    data = data_structure()
    count = 1

    # 요소가 들어올때마다 머금고 있어야함
    url = page(target, counting)
    while len(url) > 0:
        url_data = url.popleft()
        if count >= 9:
            first = 4
        elif count >= 7:
            first = 3
        elif count >= 5:
            first = 2
        else:
            first = 1

        if url_data not in data[first][count]:
            data[first][count] = url_data

        count += 1

    return data


# DFS 함수 정의
def recursive_dfs(
    node: int, graph: dict[int, dict[int, list[str]]], discovered: list[int] = None
) -> list[int]:
    if discovered is None:
        discovered = []

    discovered.append(node)
    for n in graph.get(node, []):
        if n not in discovered:
            recursive_dfs(n, graph, discovered)

    return discovered


# BFS 함수 정의
def iterative_bfs(start_v: int, graph: dict[int, list[str]]) -> deque[list[str]]:
    start = deque()

    visited = set()
    queue = deque([start_v])
    visited.add(start_v)
    while queue:
        node = queue.popleft()
        if graph.get(node, []):
            start.append(graph[node])
            if node not in visited:
                visited.add(node)
                queue.append(node)

    return start


def deep_dive_search(
    page: Callable[[str, int], deque[list[str]]],
    target: str,
    counting: int,
    objection: str,
) -> deque[list[str]]:
    starting_queue = deque()
    tree: dict[int, dict[int, list[str]]] = indstrict(page, target, counting)
    dfs: list[str] = recursive_dfs(1, tree)

    print(f"{objection}의 검색된 노드의 순서 --> {dfs}")
    for location in dfs:
        try:
            element = tree[location]
            for num in element.keys():
                urls: list[str] = iterative_bfs(num, element).pop()
                starting_queue.append(urls)
        except (KeyError, IndexError):
            continue
    return starting_queue


async def url_classifier(url: str, status: int) -> None:
    match status:
        case 200:
            ready_queue.append(url)
        case _:
            not_request_queue.append({status: url})


async def fetch_status(url: str) -> tuple[str, int]:
    connector = aiohttp.TCPConnector()
    async with aiohttp.ClientSession(connector=connector, trust_env=True) as session:
        async with session.get(url) as response:
            await asyncio.sleep(0.25)
            if response.status == 200:
                return url, response.status
            else:
                return url, response.status


async def aiorequest_injection(start: deque[list[str]], batch_size: int) -> None:
    while start:
        node: list[str] = start.popleft()
        if len(node) > 0:
            print(f"묶음 처리 진행합니다 --> {len(node)}개 진행합니다 ")
            for count in range(0, len(node), batch_size):
                batch: list[str] = node[count : count + batch_size]

                tasks: list[Coroutine[tuple[str, int]]] = [
                    fetch_status(url) for url in batch
                ]
                results: list[tuple[str, int]] = await asyncio.gather(
                    *tasks, return_exceptions=True
                )

                for url_collect in results:
                    if isinstance(url_collect, tuple):
                        url, status = url_collect
                        await url_classifier(url, status)
                    else:
                        print(f"Type 불일치: {url_collect}")


def process_bing(target: str, count: int) -> deque[list[str]]:
    return BingMovingElementLocation(target, count).repeat_scroll()


def process_google(target: str, count: int) -> deque[list[str]]:
    return GoogleMovingElementsLocation(target, count).search_box()


with ThreadPoolExecutor(2) as poll:
    task = [
        poll.submit(deep_dive_search, process_google, "BTC", 10, "google"),
        poll.submit(deep_dive_search, process_bing, "BTC", 10, "bing"),
    ]

    for data in as_completed(task):
        asyncio.run(aiorequest_injection(data.result(), 20))


print(len(ready_queue))
print(len(not_request_queue))
