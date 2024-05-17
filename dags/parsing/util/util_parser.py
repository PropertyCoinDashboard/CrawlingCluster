"""
파일 유틸리티
"""

from typing import Any, Union
from pathlib import Path
from urllib.parse import urlparse

import requests
import pandas as pd

from bs4 import BeautifulSoup

# from airflow.providers.mysql.hooks.mysql import MySqlHook


path_location = Path(__file__).parent.parent.parent


# def mysql_saving_hook(query: str):
#     mysql_hook = MySqlHook(mysql_conn_id="airflow-mysql")
#     mysql_hook.run(query)


# 데이터 정의


def data_structure() -> dict[int, dict[int, list[str]]]:
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


def soup_data(
    html_data: str,
    element: str,
    elements: dict[str, Union[str, list[str]]],
    soup: BeautifulSoup = None,
) -> list:
    """
    Parse the HTML data using BeautifulSoup
    """
    if soup is None:
        soup = BeautifulSoup(html_data, "lxml")

    search_results = soup.find_all(element, elements)
    return search_results if search_results else []


def url_parsing(url: str, headers: dict[str, Any]):
    """
    url parsing
    """
    response = requests.get(url, headers=headers, timeout=60)

    match response.status_code:
        case 200:
            return response.json()
        case _:
            raise requests.exceptions.RequestException(
                f"API Request에 실패하였습니다 status code --> {response.status_code}"
            )
