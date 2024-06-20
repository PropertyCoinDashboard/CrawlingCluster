import json
import builtins
import logging
import asyncio
from datetime import datetime
from itertools import chain
from collections import Counter
from typing import Any, Union, Callable

from konlpy.tag import Okt

import requests
from bs4 import BeautifulSoup
import aiohttp

from parsing.hooks.db.data_hook import KeywordExtractor
from airflow.providers.mysql.hooks.mysql import MySqlHook
from parsing.util.search import AsyncRequestAcquisitionHTML as ARAH
from MySQLdb._exceptions import DatabaseError, DataError

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def fetch_content(link: str) -> str:
    """주어진 URL에서 콘텐츠를 가져오기

    Args:
        link (str): 콘텐츠를 가져올 URL.

    Returns:
        str: 가져온 콘텐츠를 문자열 형태로 반환.
    """
    try:
        response: str = await ARAH.async_fetch_content(response_type="html", url=link)
        text: str = BeautifulSoup(response, "lxml").get_text(separator=" ", strip=True)
        return text
    except TypeError:
        return ""


def keword_preprocessing(text: str) -> list[tuple[str, int]]:
    okt = Okt()

    okt_pos = okt.pos(text, norm=True, stem=True)

    # fmt: off
    str_preprocessing = list(filter(lambda data: data if data[1] in "Noun" else None, okt_pos))
    word_collect = [i[0] for i in str_preprocessing if len(i[0]) > 1]
    word_count = Counter(word_collect).most_common(1)
    return word_count


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
        try:
            columns = (
                "status_code",
                "url",
                "title",
                "content",
                "keyword",
                "score",
                "created_at",
                "updated_at",
            )
            values = (
                200,
                data.get("link"),
                data.get("title"),
                data.get("content"),
                json.dumps(data.get("keyword"), ensure_ascii=False),
                data.get("score"),
                data.get("date"),
                datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            )
            self.insert_data("dash.request_url", columns, values)
        except (DatabaseError, DataError):
            pass

    def insert_total_url(self, urls: list[dict[str, str]]) -> None:
        """URL을 데이터베이스에 넣기.

        Args:
            urls (list[dict[str, str]]): 넣을 URL 목록.
        """
        query = "INSERT INTO dash.total_url(url, created_at) VALUES (%s, %s);"
        for url in urls:
            self.mysql_hook.run(query, parameters=(url["link"], url["date"]))

    def delete_from_database(self, table: str, url: str) -> bool:
        """
        주어진 id와 테이블명에 해당하는 레코드를 MySQL 데이터베이스에서 삭제합니다 (레코드가 존재할 경우에만).

        Args:
            table (str): 삭제할 레코드가 있는 테이블의 이름
            id (int): 삭제할 레코드의 id
        """
        # 삭제 전에 레코드가 존재하는지 확인
        select_query = f"SELECT url FROM dash.{table} WHERE url=%s"
        result = self.mysql_hook.get_records(select_query, parameters=(url,))

        if len(result) > 0:
            # 레코드가 존재할 경우 삭제 작업을 수행
            logger.info("데이터 삭제합니다")
            delete_query = f"DELETE FROM dash.{table} WHERE url=%s"
            self.mysql_hook.run(delete_query, parameters=(id,))

            return True

        return False


class URLClassifier:
    """URL을 분류하고 그에 따라 데이터베이스에 넣기"""

    def __init__(self, db_handler: DatabaseHandler) -> None:
        self.db_handler = db_handler

    async def data_checking(
        self, retry: bool, result: dict[str, str], delete_table: str, process: Callable
    ) -> dict[str, str] | None:
        if not retry:
            return result

        excutor: bool = self.db_handler.delete_from_database(
            table=delete_table, id=result.get("url")
        )
        if not excutor:
            logger.info("넘어갑니다")

        if result.get("status") == 200:
            re_data = Pipeline(self.db_handler)._context_extract(result=result)
            process(re_data)
        else:
            process(result)

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
            match type(req):
                case builtins.str:
                    result["status"] = 200
                    return await self.data_checking(
                        result=result,
                        retry=retry,
                        delete_table="not_request_url",
                        process=self.db_handler.insert_ready_status,
                    )

                case builtins.dict:
                    result["status"] = req["status"]
                    return await self.data_checking(
                        result=result,
                        retry=retry,
                        delete_table="request_url",
                        process=self.db_handler.insert_not_ready_status,
                    )

        except Exception as e:
            logger.error(f"Error occurred during request handling: {e}")
            result["status"] = 500
            result["updated_at"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            return await self.data_checking(
                result=result,
                retry=retry,
                delete_table="request_url",
                process=self.db_handler.insert_not_ready_status,
            )

    async def retry_request_classify(
        self, result: dict[str, Union[str, int]]
    ) -> dict[str, str] | None:
        """재시도를 통해 URL을 분류하고 데이터베이스에 넣기"""
        return await self.handle_async_request(result, retry=True)

    async def request_classify(
        self, result: dict[str, Union[str, int]]
    ) -> dict[str, str] | None:
        """URL을 분류하고 데이터베이스에 넣기"""
        return await self.handle_async_request(result, retry=False)


class Pipeline:
    """URL 처리를 위한 파이프라인을 실행"""

    def __init__(self, db_handler: DatabaseHandler) -> None:
        """파이프라인 초기화

        Args:
            db_handler (DatabaseHandler): 데이터베이스 핸들러
        """
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

    # fmt: off
    async def process_url(self, url: list, func: Callable) -> Any:
        """URL을 처리하여 비동기적으로 요청

        Args:
            url (list): 처리할 URL 목록
            func (Callable): URL을 처리할 함수
        """
        def lambda_process(process: chain) -> list:
            return list(map(lambda item: func(item), process))
        
        match type(url[0]):
            case builtins.tuple:
                tasks: list[dict[str, str]] = [
                    func(json.loads(*url[0][i])) for i in range(len(url[0]))
                ]
                return await asyncio.gather(*tasks, return_exceptions=False)
            case builtins.list:
                if isinstance(url[0][0], list):
                    tasks = lambda_process(chain.from_iterable(*url))
                else:
                    tasks = lambda_process(chain(*url))
                return await asyncio.gather(*tasks, return_exceptions=False)

    async def _context_extract(self, result: dict) -> dict[str, Union[int, str, float]]:
        result["content"] = await fetch_content(result["link"])
        result["keyword"] = keword_preprocessing(result["content"])
        result["score"] = KeywordExtractor(
            url=result["link"],
            text=result["content"],
            keyword=result["keyword"],
            present_time_str=result["date"],
        ).calculate_target()
        return result
    
    async def request_transfor(self, **context) -> None:
        urls = context["ti"].xcom_pull(key="request_url")
        tasks = list(map(lambda data: self._context_extract(result=data), urls))
        result: list[dict[str, str]] = await asyncio.gather(*tasks, return_exceptions=False)
        
        context["ti"].xcom_push(key="request_extraction", value=result)

    async def retry_status_classifcation(self, **context: dict[str, Any]) -> None:
        """재시도를 통해 URL 상태를 분류

        Args:
            **context (dict[str, Any]): 태스크 컨텍스트
        """
        urls = context["ti"].xcom_pull(task_ids=context["task"].upstream_task_ids)
        await self.process_url(urls, self.url_classifier.retry_request_classify)

    async def aiorequest_classification(self, **context: dict[str, Any]) -> None:
        """비동기 요청을 주입하고 분류

        Args:
            **context (dict[str, Any]): 태스크 컨텍스트
        """
        urls = context["ti"].xcom_pull(task_ids=context["task"].upstream_task_ids)
        task_instance = context["ti"]

        # 비동기 분류
        data = await self.process_url(urls, self.url_classifier.request_classify)
        request, not_request = [], []
        for item in data:
            if item and item.get("status") is not None:
                not_request.append(item)
            else:
                request.append(item)

        task_instance.xcom_push(key="request_url", value=request)
        task_instance.xcom_push(key="not_request_url", value=not_request)

    async def saving_task(self, process: Callable, urls) -> None:
        """비동기적으로 작업을 저장

        Args:
            process (Callable): 처리 함수
            urls (list): 저장할 URL 목록
        """
        if len(urls) != 0:
            await asyncio.gather(process(data) for data in urls)

    async def not_request_saving(self, **context: dict[str, Any]) -> None:
        """200을 제외한 URL을 저장

        Args:
            **context (dict[str, Any]): 태스크 컨텍스트
        """
        urls = context["ti"].xcom_pull(key="not_request_url")
        await self.saving_task(self.db_handler.insert_not_ready_status, urls)

    async def request_saving(self, **context: dict[str, Any]) -> None:
        """200 URL을 저장

        Args:
            **context (dict[str, Any]): 태스크 컨텍스트
        """
        urls = context["ti"].xcom_pull(key="request_extraction")
        await self.saving_task(self.db_handler.insert_ready_status, urls)
