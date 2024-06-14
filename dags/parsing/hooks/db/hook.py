import json
import logging
import asyncio
from typing import Any, Union, Callable
from datetime import datetime

import requests
from bs4 import BeautifulSoup

from airflow.providers.mysql.hooks.mysql import MySqlHook
from aiohttp.client_exceptions import ClientConnectorSSLError
from parsing.util.search import AsyncRequestAcquisitionHTML as ARAH

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
            data.get("updated_at"),
        )
        self.insert_data("dash.not_request_url", columns, values)

    def insert_ready_status(self, data: dict[str, str]) -> None:
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
            data.get("content"),
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

    def delete_from_database(self, table: str, id: int) -> bool | None:
        """
        주어진 id와 테이블명에 해당하는 레코드를 MySQL 데이터베이스에서 삭제합니다 (레코드가 존재할 경우에만).

        Args:
            table (str): 삭제할 레코드가 있는 테이블의 이름
            id (int): 삭제할 레코드의 id
        """
        # 삭제 전에 레코드가 존재하는지 확인
        select_query = f"SELECT 1 FROM dash.{table} WHERE id=%s"
        result = self.mysql_hook.get_records(select_query, parameters=(id,))

        if len(result) > 0:
            # 레코드가 존재할 경우 삭제 작업을 수행
            delete_query = f"DELETE FROM dash.{table} WHERE id=%s"
            self.mysql_hook.run(delete_query, parameters=(id,))

            return True

        return None


class URLClassifier:
    """URL을 분류하고 그에 따라 데이터베이스에 넣기"""

    def __init__(self, db_handler: DatabaseHandler) -> None:
        self.db_handler = db_handler

    async def handle_async_request(
        self, result: dict[str, str], retry: bool | None
    ) -> dict[str, str] | None:
        """
        Args:
            result (dict[str, str]): 처리할 결과를 담은 사전. 'link'와 'id'를 포함.

        - 비동기 요청을 처리하는 함수.
            - 'link' 키를 통해 요청 상태를 조회.
                - 요청이 str인 경우, 'not_request_url' 테이블에서 해당 항목을 삭제하고
                    - 콘텐츠를 가져와 'ready_status'로 저장.
                - 요청이 dict인 경우, 'request_url' 테이블에서 해당 항목을 삭제하고
                    - 상태 값을 'not_ready_status'로 저장.
                - 요청 예외 발생 시, 오류 로그를 기록하고 상태를 500으로 설정하여
                    - 'not_ready_status'로 저장.
        """
        try:
            link: str | None = result.get("link")
            req: str | dict[str, int] | dict[str, str] = (
                await ARAH.async_request_status(link)
            )
            result["updated_at"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            match req:
                case str():
                    content: str = fetch_content(link)
                    result["content"] = content

                    if retry:
                        excutor: bool | None = self.db_handler.delete_from_database(
                            table="not_request_url", id=result.get("id")
                        )
                        if excutor:
                            self.db_handler.insert_ready_status(result, content)
                        else:
                            pass

                    if retry is None:
                        return result
                case dict():
                    result["status"] = req["status"]
                    if retry:
                        excutor: bool | None = self.db_handler.delete_from_database(
                            table="request_url", id=result.get("id")
                        )
                        if excutor:
                            self.db_handler.insert_not_ready_status(result)
                        else:
                            pass

                    if retry is None:
                        return result

        except (requests.exceptions.RequestException, ClientConnectorSSLError) as e:
            logger.error(f"Error occurred during request handling: {e}")
            result["status"] = 500
            result["updated_at"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            return result

    async def retry_request_classify(
        self, result: dict[str, Union[str, int]]
    ) -> dict[str, str] | None:
        """재시도를 통해 URL을 분류하고 데이터베이스에 넣기"""
        return await self.handle_async_request(result, retry=True)

    async def request_classify(
        self, result: dict[str, Union[str, int]]
    ) -> dict[str, str] | None:
        """재시도를 통해 URL을 분류하고 데이터베이스에 넣기"""
        return await self.handle_async_request(result, retry=None)


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

    async def process_url(self, url: list[list[dict]], class_func: Callable) -> None:
        data = []
        for type_list_1 in url:
            for type_list_2 in type_list_1:
                if class_func.__name__ == "request_classify":
                    data.append(await class_func(type_list_2))
                if class_func.__name__ == "retry_request_classify":
                    class_func(type_list_2)
        return data

    async def retry_status_classifcation(self, **context: dict[str, Any]) -> None:
        urls = context["ti"].xcom_pull(task_ids=context["task"].upstream_task_ids)
        address = self.url_classifier.retry_request_classify
        await asyncio.gather(self.process_url(url=urls, class_func=address))

    async def aiorequest_classification(self, **context: dict[str, Any]) -> None:
        """비동기 요청을 주입하고 분류

        Args:
            **context (dict[str, Any]): 태스크 컨텍스트.
        """
        urls = context["ti"].xcom_pull(task_ids=context["task"].upstream_task_ids)
        task_instance = context["ti"]

        request = []
        not_request = []
        address = self.url_classifier.request_classify

        data = await asyncio.gather(
            self.process_url(urls, address), return_exceptions=True
        )
        for i in data:
            for j in i:
                if j.get("status") is not None:
                    not_request.append(j)
                else:
                    request.append(j)

        task_instance.xcom_push(key="request_url", value=request)
        task_instance.xcom_push(key="not_request_url", value=not_request)

    async def saving_task(self, process: Callable, urls) -> None:
        if len(urls) != 0:
            await asyncio.gather(process(data) for data in urls[0])

    async def not_request_saving(self, **context) -> None:
        urls = context["ti"].xcom_pull(key="not_request_url")
        await self.saving_task(self.db_handler.insert_not_ready_status, urls)

    async def request_saving(self, **context) -> None:
        urls = context["ti"].xcom_pull(key="request_url")
        await self.saving_task(self.db_handler.insert_ready_status, urls)
