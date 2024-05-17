"""
기능 테스트
Airflow 발전시키기
"""

import requests
from typing import Callable
from collections import deque
from parsing.util.util_parser import data_structure
from concurrent.futures import ThreadPoolExecutor, as_completed
from parsing.selenium_parsing import (
    GoogleMovingElementsLocation,
    BingMovingElementLocation,
)


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


# BFS 함수 정의
import time


def iterative_bfs(start_v: int, graph: dict[int, list[str]], target: str) -> None:
    visited = set()
    queue = deque([start_v])
    visited.add(start_v)
    while queue:
        node = queue.popleft()
        time.sleep(1)
        for neighbor in graph.get(node, []):
            time.sleep(1)
            print(
                f"BFS visiting node: {target} -- {node} -- {neighbor[:20]} -> {requests.get(neighbor).status_code}"
            )
            if neighbor not in visited:
                visited.add(neighbor)
                queue.append(neighbor)


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


def process_bing(target: str, count: int) -> None:
    return BingMovingElementLocation(target, count).repeat_scroll()


def process_google(target: str, count: int) -> deque[list[str]]:
    return GoogleMovingElementsLocation(target, count).search_box()


def deep_dive_search(
    page: Callable[[str, int], deque[list[str]]],
    target: str,
    counting: int,
    objection: str,
):
    tree = indstrict(page, target, counting)
    dfs = recursive_dfs(1, tree)
    print(f"{objection}의 검색된 노드의 순서 --> {dfs}")
    print(f"{objection} 탐색 시작합니다")
    for data in dfs:
        try:
            element = tree[data]
            for num in element.keys():
                iterative_bfs(num, element, objection)
        except KeyError:
            continue


with ThreadPoolExecutor(2) as poll:
    task = [
        poll.submit(deep_dive_search, process_google, "BTC", 10, "google"),
        poll.submit(deep_dive_search, process_bing, "BTC", 10, "bing"),
    ]

    for data in as_completed(task):
        data.result()
