# aiohttp.client_exceptions.ClientConnectorSSLError:
# Cannot connect to host www.gameshot.net:443 ssl:default [[SSL: DH_KEY_TOO_SMALL] dh key too small (_ssl.c:1006)]

from datetime import datetime
from typing import Any, Union
from bs4 import BeautifulSoup
import requests
import logging

from airflow.providers.mysql.hooks.mysql import MySqlHook
from parsing.util.search import AsyncRequestAcquisitionHTML as ARAH
from aiohttp.client_exceptions import ClientConnectorSSLError

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def fetch_content(link: str) -> str:
    """주어진 URL에서 콘텐츠를 가져오기

    Args:
        link (str): 콘텐츠를 가져올 URL.

    Returns:
        str: 가져온 콘텐츠를 문자열 형태로 반환.
    """
    response = requests.get(link)
    response.encoding = response.apparent_encoding
    return BeautifulSoup(response.text, "lxml").get_text(strip=True)


class DatabaseHandler:
    """데이터베이스와의 상호작용을 처리"""

    def __init__(self, mysql_conn_id: str = "airflow-mysql") -> None:
        self.mysql_hook = MySqlHook(mysql_conn_id=mysql_conn_id)

    def insert_data(
        self, table: str, columns: tuple[str], values: tuple[Union[int, str, None]]
    ) -> None:
        """데이터를 데이터베이스에 삽입.

        Args:
            table (str): 테이블 이름.
            columns (tuple): 삽입할 컬럼들.
            values (tuple): 삽입할 값들.
        """
        column_str = ", ".join(columns)
        value_placeholders = ", ".join(["%s"] * len(values))
        query = f"INSERT INTO {table} ({column_str}) VALUES ({value_placeholders})"

        self.mysql_hook.run(query, parameters=values)

    def insert_not_ready_status(self, data: dict[str, Union[int, str]]) -> None:
        """아직 준비되지 않은 URL에 대한 데이터를 데이터베이스에 삽입.

        Args:
            data (dict[str, Union[int, str]]): 넣을 데이터.
        """
        columns = ("status_code", "url", "title", "created_at", "updated_at")
        values = (
            data.get("status"),
            data.get("link"),
            data.get("title"),
            data.get("date"),
            datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        )
        self.insert_data("dash.not_request_url", columns, values)

    def insert_ready_status(self, data: dict[str, str], content: str) -> None:
        """준비된 URL에 대한 데이터를 데이터베이스에 넣음.

        Args:
            data (dict[str, str]): 넣을 데이터.
            content (str): URL의 콘텐츠.
        """
        columns = ("status_code", "url", "title", "content", "created_at", "updated_at")
        values = (
            200,
            data.get("link"),
            data.get("title"),
            content,
            data.get("date"),
            datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        )
        self.insert_data("dash.request_url", columns, values)

    def insert_total_url(self, urls: list[dict[str, str]]) -> None:
        """URL을 데이터베이스에 넣기.

        Args:
            urls (list[dict[str, str]]): 넣을 URL 목록.
        """
        query = "INSERT INTO dash.total_url(url, created_at) VALUES (%s, %s);"
        for url in urls:
            self.mysql_hook.run(query, parameters=(url["link"], url["date"]))


class URLClassifier:
    """URL을 분류하고 그에 따라 데이터베이스에 넣기"""

    def __init__(self, db_handler: DatabaseHandler) -> None:
        self.db_handler = db_handler

    async def classify(self, result: dict[str, str]) -> None:
        """URL을 분류하고 데이터베이스에 넣기

        Args:
            result (dict[str, str]): 분류하고 넣을 URL 데이터.
        """
        link: str | None = result.get("link")
        try:
            req: str | dict[str, int] | dict[str, str] = (
                await ARAH.async_request_status(link)
            )
            match req:
                case str():
                    content: str = fetch_content(link)
                    self.db_handler.insert_ready_status(result, content)
                case dict():
                    result["status"] = req["status"]
                    self.db_handler.insert_not_ready_status(result)
        except (requests.exceptions.RequestException, ClientConnectorSSLError) as e:
            result["status"] = 500
            self.db_handler.insert_not_ready_status(result)


class Pipeline:
    """URL 처리를 위한 파이프라인을 실행"""

    def __init__(self, db_handler: DatabaseHandler) -> None:
        self.db_handler = db_handler
        self.url_classifier = URLClassifier(db_handler)

    def first_data_saving(self, **context: dict[str, Any]) -> None:
        """초기 데이터를 데이터베이스에 저장

        Args:
            **context (dict[str, Any]): 태스크 컨텍스트
        """
        urls = context["ti"].xcom_pull(task_ids=context["task"].upstream_task_ids)
        for data in urls:
            self.db_handler.insert_total_url(data)

    async def aiorequest_injection(self, **context: dict[str, Any]) -> None:
        """비동기 요청을 주입하고 분류

        Args:
            **context (dict[str, Any]): 태스크 컨텍스트.
        """
        urls = context["ti"].xcom_pull(task_ids=context["task"].upstream_task_ids)
        for data in urls:
            for tud in data:
                await self.url_classifier.classify(tud)
