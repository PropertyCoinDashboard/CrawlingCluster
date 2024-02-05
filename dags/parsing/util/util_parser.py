"""
파일 유틸리티
"""

from typing import Any, Union
from pathlib import Path
from urllib.parse import urlparse

import aiohttp
import pandas as pd

from bs4 import BeautifulSoup
from parsing.util.create_log import log

path_location = Path(__file__).parent.parent.parent


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


# 비동기 연결
async def url_parsing(url: str, headers: dict[str, Any]):
    """
    url parsing
    """
    async with aiohttp.ClientSession() as session:
        async with session.get(url, headers=headers) as resp:
            if resp.status == 200:
                return await resp.json()
            elif resp.status != 200:
                raise aiohttp.ClientError(
                    f"API Request에 실패하였습니다 status code --> {resp.status}"
                )


# API 호출해올 비동기 함수 (Naver, Daum)
## 함수에 너무 많은 책임이 부여되어 있어 분할 필요성 느낌
async def get_news_data(
    target: str,
    items: str,
    titles: str,
    link: str,
    target_url: str,
    build_header: dict[str, str],
):
    """new parsing

    Args:
        target (str): 타겟 API
        items (str): 첫번째 접근
        title (str): 타이틀
        link (str): url
        target_url (str): 파싱하려는 API
        build_header (dict[str, str]): 인증 헤더값

    Returns:
        _type_: str
    """
    logger = log(f"{target}", f"{path_location}/log/info.log")
    res_data = await url_parsing(target_url, build_header)

    count = 0
    for item in res_data[items]:
        title = item[titles]
        url = item[link]
        count += 1

        logger.info("%s Title: %s", target, title)
        logger.info("%s URL: %s", target, url)
        logger.info("--------------------")
    logger.info("%s parsing data --> %s", target, count)
