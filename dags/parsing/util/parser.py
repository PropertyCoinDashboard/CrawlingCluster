"""
파일 유틸리티
"""

import re
import aiohttp
import asyncio
import inspect
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


def soup_data(
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
    if inspect.iscoroutine(url):
        url = asyncio.run(url)

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
