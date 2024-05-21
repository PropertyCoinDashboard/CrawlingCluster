"""
파일 유틸리티
"""

import aiohttp
import re
from collections import deque
from typing import Any
from pathlib import Path
from urllib.parse import urlparse


import pandas as pd
from bs4 import BeautifulSoup
from parsing.util._typing import (
    UrlDataStructure,
    DataStructure,
    SeleniumUrlCollect,
    UrlCollect,
    OuterData,
)

# from airflow.providers.mysql.hooks.mysql import MySqlHook


path_location = Path(__file__).parent.parent.parent


# def mysql_saving_hook(query: str):
#     mysql_hook = MySqlHook(mysql_conn_id="airflow-mysql")
#     mysql_hook.run(query)


# 데이터 정의


def data_structure() -> DataStructure:
    """데이터 묶기 위한 트리 구조 추상화

    Returns:
        DataStructure: {
            1: {1: [], 2: [],3: [], 4: []},
            2: {5: [], 6:[]},
            3: {7: [], 8:[]},
            4: {9: [], 10: []},
        }
    """
    return {
        i: (
            {j: [] for j in range(1, 5)}
            if i == 1
            else (
                {j: [] for j in range(5, 7)}
                if i == 2
                else (
                    {j: [] for j in range(7, 9)}
                    if i == 3
                    else {j: [] for j in range(9, 11)}
                )
            )
        )
        for i in range(1, 5)
    }


def csv_saving(data: list, csv_file_name: str) -> pd.DataFrame:
    """coin symbol csv saving

    Args:
        data (list): coinsymbol
        csv_file_name (str): 파일명

    Returns:
        pd.DataFrame: dataframe
    """
    return pd.DataFrame(data).to_csv(csv_file_name, index_label=False, index=False)


def url_create(url: str) -> str:
    """url 합성
    Args:
        url (str): url

    Returns:
        str: 완품 url
            - ex) naver.com -> https://www.naver.com
    """
    return f"{urlparse(url).scheme}://{urlparse(url).netloc}/"


def url_addition(url: str) -> str:
    """/~ 로 끝나는 url 붙여주는 함수
    Args:
        url (str): url

    Returns:
        str: url
    """
    link = url_create(url) + url if url.startswith("/") else url
    return link


async def soup_data(
    html_data: str,
    element: str,
    elements: Any | None,
    soup: BeautifulSoup = None,
) -> list:
    """
    Parse the HTML data using BeautifulSoup
    """
    if soup is None:
        soup = BeautifulSoup(html_data, "lxml")

    search_results = soup.find_all(element, elements)
    return search_results if search_results else []


def href_from_text_preprocessing(text: str) -> str:
    """텍스트 전처리

    Args:
        text (str): URL title 및 시간
            - ex) 어쩌구 저쩌구...12시간

    Returns:
        str: 특수문자 및 시간제거
            - ex) 어쩌구 저쩌구
    """
    return re.sub(r"\b\d+시간 전\b|\.{2,}|[^\w\s]", "", text)


def href_from_a_tag(a_tag: BeautifulSoup, element: str = "href") -> str:
    """URL 뽑아내기

    Returns:
        str: [URL, ~~]
    """
    return a_tag.get(element)


def indstrict(page: SeleniumUrlCollect, target: str, counting: int) -> UrlDataStructure:
    """

    Args:
        page (SeleniumUrlCollect): 각 웹페이지에서 selenium을 이용해서 URL 긁어옴
        target (str): 긁어올 대상
        counting (int): 몇번 스크래핑 진행할건지

    Returns:
        UrlDataStructure:
        - \n {
            1: {1: [url 대상들], 2: [url 대상들],3: [url 대상들], 4: [url 대상들]},
            2: {5: [url 대상들], 6:[url 대상들]},
            3: {7: [url 대상들], 8:[url 대상들]},
            4: {9: [url 대상들], 10: [url 대상들]},
        }

    """
    data: DataStructure = data_structure()
    count = 1

    # 요소가 들어올때마다 머금고 있어야함
    url: UrlCollect = page(target, counting)
    while len(url) > 0:
        url_data: list[str] = url.popleft()
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
    node: int, graph: UrlDataStructure, discovered: list = []
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


def deep_dive_search(
    page: SeleniumUrlCollect,
    target: str,
    counting: int,
    objection: str,
) -> UrlCollect:
    starting_queue = deque()
    tree: UrlDataStructure = indstrict(page, target, counting)
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
        url: str,
        params: dict[str, str] | None = None,
        headers: dict[str, str] | None = None,
    ):
        async with aiohttp.ClientSession() as session:
            return await AsyncRequestAcquisitionHTML(
                session, url, params, headers
            ).async_html_source()

    async def async_html_source(self) -> str:
        async with self.session.get(
            url=self.url, params=self.params, headers=self.headers
        ) as response:
            return await response.text()

    async def asnyc_status_classifer(self) -> tuple[str, int]:
        async with self.session.get(
            url=self.url, params=self.params, headers=self.headers
        ) as response:
            match response.status:
                case 200:
                    return self.url, response.status
                case _:
                    return self.url, response.status
