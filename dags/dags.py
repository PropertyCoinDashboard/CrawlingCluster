import asyncio
from datetime import datetime, timedelta

from airflow import DAG
from airflow.operators.bash import BashOperator
from airflow.operators.python import PythonOperator
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


def async_process_injection(**context) -> list:
    loop = asyncio.get_event_loop()
    if loop.is_running():
        loop.run_until_complete(context["process"](**context))
    else:
        asyncio.run(context["process"](**context))


default_args = {
    "owner": "airflow",
    "depends_on_past": False,
    "start_date": datetime(2024, 6, 10),
    "email": ["limhaneul12@naver.com"],
    "email_on_failure": False,
    "email_on_retry": False,
    "retries": 1,
    "retry_delay": timedelta(minutes=10),
}


with DAG(
    dag_id="Crawling_data_API",
    default_args=default_args,
    schedule_interval=timedelta(minutes=10),
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
        python_callable=async_process_injection,
        op_kwargs={"process": pipeline.aiorequest_classification},
        provide_context=True,
        dag=dag,
    )

    not_request = PythonOperator(
        task_id="not_request",
        python_callable=async_process_injection,
        op_kwargs={"process": pipeline.not_request_saving},
        provide_context=True,
        dag=dag,
    )

    request_200 = PythonOperator(
        task_id="200_request",
        python_callable=async_process_injection,
        op_kwargs={"process": pipeline.request_saving},
        provide_context=True,
        dag=dag,
    )

    saving = PythonOperator(
        task_id="saving", python_callable=first_data_saving_task, dag=dag
    )

    response >> wait_for_api_response >> start_operator >> naver >> saving
    naver >> status_requesting >> not_request
    naver >> status_requesting >> request_200

with DAG(
    dag_id="deep_data_API",
    default_args=default_args,
    schedule=None,
    schedule_interval=None,
    tags=["딥 크롤링"],
) as dag:

    url_selection = MySqlOperator(
        task_id="mysql_query",
        mysql_conn_id="airflow-mysql",
        sql="SELECT url FROM dash.request_url;",
        dag=dag,
    )

    hooking = PythonOperator(
        task_id="list_change",
        python_callable=data_list_change,
        provide_context=True,
        dag=dag,
    )
    th = PythonOperator(
        task_id="async_change",
        python_callable=async_process_injection,
        op_kwargs={"process": deep_crawling_run},
        provide_context=True,
        dag=dag,
    )

    prepro = PythonOperator(
        task_id="dddd", python_callable=preprocessing, provide_context=True, dag=dag
    )

    status_requesting = PythonOperator(
        task_id="deep_classifier",
        python_callable=async_process_injection,
        op_kwargs={"process": pipeline.aiorequest_classification},
        provide_context=True,
        dag=dag,
    )

    not_request = PythonOperator(
        task_id="dee_not_request",
        python_callable=async_process_injection,
        op_kwargs={"process": pipeline.not_request_saving},
        provide_context=True,
        dag=dag,
    )

    request_200 = PythonOperator(
        task_id="deee200_request",
        python_callable=async_process_injection,
        op_kwargs={"process": pipeline.request_saving},
        provide_context=True,
        dag=dag,
    )

    (
        url_selection
        >> hooking
        >> th
        >> prepro
        >> status_requesting
        >> not_request
        >> request_200
    )


def create_url_status_dag(dag_id, query_table) -> DAG:
    with DAG(
        dag_id=dag_id,
        default_args=default_args,
        schedule_interval=timedelta(minutes=10),
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
            provide_context=True,
            dag=dag,
        )

        url_selection >> process_url_data_task

    return dag


dag1 = create_url_status_dag("another_request_check", "not_request_url")
dag2 = create_url_status_dag("200_request_check", "request_url")
