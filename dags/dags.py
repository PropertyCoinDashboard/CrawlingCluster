import asyncio
from typing import Callable

import pytz
from datetime import datetime, timedelta

from airflow import DAG
from airflow.operators.bash import BashOperator
from airflow.operators.python import PythonOperator
from airflow.operators.trigger_dagrun import TriggerDagRunOperator
from airflow.utils.task_group import TaskGroup
from airflow.sensors.external_task import ExternalTaskSensor
from airflow.providers.mysql.operators.mysql import MySqlOperator
from parsing.drive.naver_parsing_api import NaverNewsParsingDriver
from parsing.operators.crawling import CrawlingOperator
from parsing.hooks.db.hook import DatabaseHandler, Pipeline
from parsing.hooks.db.data_hook import (
    data_list_change,
    deep_crawling_run,
    preprocessing,
)


db_handler = DatabaseHandler()
pipeline = Pipeline(db_handler)


def response_html(search_keyword: str, count: int) -> dict[str, bool]:
    data = NaverNewsParsingDriver(search_keyword, count).fetch_page_urls()
    loop = asyncio.get_event_loop()
    play = loop.run_until_complete(data)

    if play[1] == True:
        return {"search_keyword": search_keyword, "count": count}
    else:
        return {"check_fn": False}


def first_data_saving_task(**context) -> None:
    pipeline.first_data_saving(**context)


def async_process_injection(**context) -> list:
    loop = asyncio.get_event_loop()
    if loop.is_running():
        loop.run_until_complete(context["process"](**context))
    else:
        asyncio.run(context["process"](**context))


def create_status_task(task_group_name: str, dag: DAG, pipeline: Pipeline) -> TaskGroup:
    with TaskGroup(task_group_name, dag=dag) as group:

        def create_python_operator(task_id: str, python_callable: Callable):
            return PythonOperator(
                task_id=task_id,
                python_callable=async_process_injection,
                op_kwargs={"process": python_callable},
                dag=dag,
            )

        # fmt: off
        requesting = create_python_operator("classifier", pipeline.aiorequest_classification)
        not_request = create_python_operator("not_request", pipeline.not_request_saving)
        request_200 = create_python_operator("200_request", pipeline.request_saving)
        request_extarct = create_python_operator(
            "200_request_extarct", pipeline.request_transfor
        )

        # Define task dependencies
        requesting >> not_request
        requesting >> request_extarct >> request_200

    return group


now = datetime.now()
next_run = now + timedelta(days=1)  # 다음 날로 넘어가기 위해 days=1 추가
next_run = datetime(
    next_run.year,
    next_run.month,
    next_run.day,
    hour=8,
    minute=0,
)  # 아침 8시 설정
next_run = pytz.utc.localize(next_run).astimezone(pytz.timezone("Asia/Seoul"))


default_args = {
    "owner": "airflow",
    "depends_on_past": False,
    "start_date": next_run,
    "email": ["limhaneul12@naver.com"],
    "email_on_failure": False,
    "email_on_retry": False,
    "retries": 1,
    "retry_delay": timedelta(minutes=10),
}


with DAG(
    dag_id="Crawling_data_API",
    default_args=default_args,
    schedule_interval=timedelta(hours=12),
    catchup=False,
    tags=["네이버 크롤링"],
) as dag:

    response = PythonOperator(
        task_id="api_call_task",
        python_callable=response_html,
        op_kwargs={"search_keyword": "BTC", "count": 10},
        dag=dag,
    )

    wait_for_api_response = ExternalTaskSensor(
        task_id="wait_for_api_response",
        external_dag_id="Crawling_data_API",
        external_task_id=response.task_id,
        mode="reschedule",
        poke_interval=60,
        timeout=600,
        retries=3,
        dag=dag,
    )

    start_operator = BashOperator(
        task_id="News_API_start",
        bash_command="echo crawling start!!",
        dag=dag,
    )

    naver = CrawlingOperator(
        task_id="naver_task",
        count="{{ task_instance.xcom_pull(task_ids='api_call_task')['count'] }}",
        target="{{ task_instance.xcom_pull(task_ids='api_call_task')['search_keyword'] }}",
        site="naver",
        dag=dag,
    )

    saving = PythonOperator(
        task_id="saving", python_callable=first_data_saving_task, dag=dag
    )

    status_tasks = create_status_task(
        task_group_name="status_task", dag=dag, pipeline=pipeline
    )

    trigger_deep_data_api = TriggerDagRunOperator(
        task_id="trigger_deep_data_api",
        trigger_dag_id="deep_data_API",
        dag=dag,
    )

    (response >> wait_for_api_response >> start_operator >> naver >> saving)
    naver >> status_tasks >> trigger_deep_data_api


default_args2 = {
    "owner": "airflow",
    "depends_on_past": False,
    "email": ["limhaneul12@naver.com"],
    "email_on_failure": False,
    "email_on_retry": False,
    "retries": 1,
    "retry_delay": timedelta(minutes=10),
}
with DAG(
    dag_id="deep_data_API",
    default_args=default_args2,
    schedule=None,
    schedule_interval=None,
    tags=["딥 크롤링"],
) as dag:

    url_selection = MySqlOperator(
        task_id="mysql_query",
        mysql_conn_id="airflow-mysql",
        sql="SELECT url FROM dash.request_url",
        dag=dag,
    )

    hooking = PythonOperator(
        task_id="list_change",
        python_callable=data_list_change,
        dag=dag,
    )
    th = PythonOperator(
        task_id="async_change",
        python_callable=async_process_injection,
        op_kwargs={"process": deep_crawling_run},
        dag=dag,
    )

    prepro = PythonOperator(
        task_id="preprocess",
        python_callable=preprocessing,
        dag=dag,
    )

    status_tasks = create_status_task(
        task_group_name="deep_status_task", dag=dag, pipeline=pipeline
    )

    (url_selection >> hooking >> th >> prepro >> status_tasks)


def create_url_status_dag(dag_id, query_table) -> DAG:
    with DAG(
        dag_id=dag_id,
        default_args=default_args,
        schedule_interval=timedelta(hours=6),
        catchup=False,
        tags=["URL status 분석"],
    ) as dag:
        url_selection = MySqlOperator(
            task_id="first_mysql_query",
            mysql_conn_id="airflow-mysql",
            sql=f"""
                SELECT 
                    JSON_OBJECT(
                        "id", id, 
                        "link", url, 
                        "title", title, 
                        "date", TIMESTAMP(created_at)
                    ) 
                FROM 
                    dash.{query_table};
                """,
            dag=dag,
        )

        process_url_data_task = PythonOperator(
            task_id="process_url_data",
            python_callable=async_process_injection,
            op_kwargs={"process": pipeline.retry_status_classifcation},
            dag=dag,
        )

        url_selection >> process_url_data_task

    return dag


dag1 = create_url_status_dag("another_request_check", "not_request_url")
dag2 = create_url_status_dag("200_request_check", "request_url")
