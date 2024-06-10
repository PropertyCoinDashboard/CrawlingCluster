from bs4 import BeautifulSoup
import requests

from datetime import datetime
from typing import Any
from airflow.providers.mysql.hooks.mysql import MySqlHook
from parsing.util.search import AsyncRequestAcquisitionHTML as ARAH

mysql_hook = MySqlHook(mysql_conn_id="airflow-mysql")


def not_ready_status(data: dict[str, int]) -> None:
    query = "INSERT INTO dash.not_request_url(status_code, url, title, created_at, updated_at) VALUES (%s, %s, %s, %s, %s)"
    mysql_hook.run(
        query,
        parameters=(
            data.get("status"),
            data.get("link"),
            data.get("title"),
            data.get("date"),
            datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        ),
    )


# 데이터 적재 하기 위한 추상화
def ready_request_status(data: dict[str]) -> None:
    print(data)
    query = """
    INSERT INTO dash.request_url (status_code, url, title, content, created_at, updated_at) 
    VALUES (%s, %s, %s, %s, %s, %s)
    """
    link = data.get("link")
    req = requests.get(link).text
    bs = BeautifulSoup(req, "html.parser").get_text(strip=True)
    mysql_hook.run(
        query,
        parameters=(
            200,
            data.get("link"),
            data.get("title"),
            bs,
            data.get("date"),
            datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        ),
    )


def connection_hook(url: list[dict[str]]) -> None:
    for i in url:
        query = "INSERT INTO dash.total_url(url, created_at) VALUES (%s, %s);"
        mysql_hook.run(query, parameters=(i["link"], i["date"]))


def first_data_saving(**context: dict[str, Any]) -> None:
    urls = context["ti"].xcom_pull(task_ids=context["task"].upstream_task_ids)
    for data in urls:
        connection_hook(data)


async def url_classifier(result: dict[str]) -> None:
    """객체에서 받아온 URL 큐 분류"""
    link = result.get("link")

    req: str | dict[str, int] = await ARAH.asnyc_request(link)
    match req:
        case str():
            ready_request_status(result)
        case dict():
            result["status"] = req["status"]
            not_ready_status(result)


async def aiorequest_injection(**context: dict[str, Any]) -> None:
    """starting queue에 담기 위한 시작

    Args:
        start (UrlCollect): 큐
        batch_size (int): 묶어서 처리할 량
    """
    urls = context["ti"].xcom_pull(task_ids=context["task"].upstream_task_ids)

    for data in urls:
        for tud in data:
            await url_classifier(tud)
