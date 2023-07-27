"""
파일 유틸리티
"""

from urllib.parse import urlparse
import pandas as pd


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


if __name__ == "__main__":
    a = url_create("naver")
    print(a)
