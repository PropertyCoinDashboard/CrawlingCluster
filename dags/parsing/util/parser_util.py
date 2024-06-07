"""
파일 유틸리티
"""

import re
import datetime
from typing import Any
from pathlib import Path
from urllib.parse import urlparse


import pandas as pd
from bs4 import BeautifulSoup


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


def time_extract(format: str) -> str:
    # 날짜와 시간 문자열을 datetime 객체로 변환
    date_obj = datetime.datetime.strptime(format, "%a, %d %b %Y %H:%M:%S %z")

    # 원하는 형식으로 변환
    formatted_date = date_obj.strftime("%Y-%m-%d")
    return formatted_date


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
    파싱 본체
    """
    if soup is None:
        soup = BeautifulSoup(html_data, "lxml")

    search_results = soup.find_all(element, elements)
    return search_results if search_results else []
