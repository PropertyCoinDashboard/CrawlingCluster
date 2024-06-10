# import asyncio
# from typing import Any

# from airflow import DAG
# from airflow.utils.dates import days_ago
# from airflow.utils.trigger_rule import TriggerRule
# from airflow.operators.python import PythonOperator, BranchPythonOperator
# from airflow.operators.bash import BashOperator


# with DAG(
#     dag_id="Crawling_data_API", start_date=days_ago(5), schedule_interval=None
# ) as dag:
#     from parsing.hooks.db.hook import first_data_saving
#     from parsing.asnyc_protocol import aiorequest_injection
#     from parsing.operators.crawling import CrawlingOperator
#     from parsing.operators.selenium_operators import SeleniumOperator

#     def status_200_injection(**context: dict[str, Any]) -> None:
#         data = context["ti"].xcom_pull(task_ids=context["task"].upstream_task_ids)
#         loop = asyncio.get_event_loop()
#         for i in data:
#             loop.run_until_complete(aiorequest_injection(i, 20))

#     def check_xcom_data(**context):
#         ti = context["ti"]
#         google_task_output = ti.xcom_pull(task_ids="crawl_google")
#         if isinstance(google_task_output, list) and not google_task_output:
#             return "google_2nd_task"

#     start_operator = BashOperator(
#         task_id="News_API_start", bash_command="echo crawling start!!", dag=dag
#     )

#     crawl_tasks = []
#     for site in ["naver", "daum"]:
#         crawl_task = CrawlingOperator(
#             task_id=f"crawl_{site}",
#             count=10,
#             target="BTC",
#             site=site,
#             dag=dag,
#         )
#         start_operator >> crawl_task
#         crawl_tasks.append(crawl_task)

#     google_task = CrawlingOperator(
#         task_id="crawl_google",
#         count=10,
#         target="BTC",
#         site="google",
#         dag=dag,
#     )

#     check_xcom_task = BranchPythonOperator(
#         task_id="check_xcom_task",
#         python_callable=check_xcom_data,
#         provide_context=True,
#         dag=dag,
#     )

#     google_2nd_task = SeleniumOperator(
#         task_id="google_2nd_task",
#         count=10,
#         target="BTC",
#         site="google_s",
#         dag=dag,
#     )

#     saving = PythonOperator(
#         task_id="total_data_saving",
#         python_callable=first_data_saving,
#         provide_context=True,
#         trigger_rule=TriggerRule.ALL_DONE,
#         dag=dag,
#     )

#     start_operator >> crawl_tasks
#     start_operator >> google_task
#     for crawl_task in crawl_tasks:
#         crawl_task >> saving

#     google_task >> saving
#     google_task >> check_xcom_task >> google_2nd_task >> saving
import asyncio
import tracemalloc
from typing import Coroutine
from parsing.util.search import AsyncWebCrawler, AsyncRequestAcquisitionHTML as ARAH
from parsing.drive.naver_parsing_api import NaverNewsParsingDriver

tracemalloc.start()


async def url_classifier(result) -> None:
    """객체에서 받아온 URL 큐 분류"""
    if isinstance(result, str):
        not_ready_status(result)
    elif isinstance(result, dict):
        print(result)


async def aiorequest_injection(start: list[str]) -> None:
    """starting queue에 담기 위한 시작

    Args:
        start (UrlCollect): 큐
        batch_size (int): 묶어서 처리할 량
    """
    while start:
        node: list[str] = start.pop()["link"]
        tasks: list[Coroutine[str | dict[str, int]]] = await ARAH.asnyc_request(node)
        await url_classifier(tasks)


def not_ready_status(url):
    a = asyncio.create_task(AsyncWebCrawler(url, 2, 1).run())


a = asyncio.run(NaverNewsParsingDriver("BTC", 1).extract_news_urls())
asyncio.run(aiorequest_injection(a))
