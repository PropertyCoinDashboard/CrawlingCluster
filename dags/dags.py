import asyncio
from datetime import datetime, timedelta

from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.sensors.external_task import ExternalTaskSensor
from airflow.operators.bash import BashOperator

from parsing.drive.naver_parsing_api import NaverNewsParsingDriver
from parsing.operators.crawling import CrawlingOperator
from parsing.hooks.db.hook import DatabaseHandler, Pipeline


db_handler = DatabaseHandler()
pipeline = Pipeline(db_handler)


def response_html() -> dict[str, bool]:
    data = NaverNewsParsingDriver("BTC", 10).fetch_page_urls()
    loop = asyncio.get_event_loop()
    play = loop.run_until_complete(data)

    if play[1] == True:
        return {"check_fn": True}
    else:
        return {"check_fn": False}


def first_data_saving_task(**context) -> None:
    pipeline.first_data_saving(**context)


def sync_aiorequest_injection(**context) -> list[dict[str]]:
    loop = asyncio.get_event_loop()
    if loop.is_running():
        # 이미 이벤트 루프가 실행 중인 경우
        result = loop.run_until_complete(pipeline.aiorequest_injection(**context))
    else:
        # 새로운 이벤트 루프를 시작
        result = asyncio.run(pipeline.aiorequest_injection(**context))
    return result


default_args = {
    "owner": "airflow",
    "depends_on_past": False,
    "start_date": datetime(2024, 6, 10),
    "email": ["limhaneul12@naver.com"],
    "email_on_failure": True,
    "email_on_retry": True,
    "retries": 1,
    "retry_delay": timedelta(minutes=10),
}


with DAG(
    dag_id="Crawling_data_API",
    default_args=default_args,
    # schedule_interval=timedelta(minutes=5),
    catchup=False,
    tags=["네이버 크롤링"],
) as dag:

    response = PythonOperator(
        task_id="api_call_task",
        python_callable=response_html,
        provide_context=True,
    )

    wait_for_api_response = ExternalTaskSensor(
        task_id="wait_for_api_response",
        external_dag_id="Crawling_data_API",
        external_task_id=response.task_id,
        mode="reschedule",
        poke_interval=60,
        timeout=600,
        retries=3,
    )

    start_operator = BashOperator(
        task_id="News_API_start", bash_command="echo crawling start!!"
    )

    naver = CrawlingOperator(
        task_id="naver_task",
        count=10,
        target="BTC",
        site="naver",
    )

    status_requesting = PythonOperator(
        task_id="classifier",
        python_callable=sync_aiorequest_injection,
        provide_context=True,
        dag=dag,
    )

    saving = PythonOperator(
        task_id="saving", python_callable=first_data_saving_task, dag=dag
    )

    response >> wait_for_api_response >> start_operator >> naver
    naver >> saving
    naver >> status_requesting
