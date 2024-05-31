import asyncio
from typing import Any

from airflow import DAG
from airflow.utils.dates import days_ago
from airflow.utils.trigger_rule import TriggerRule
from airflow.operators.python import PythonOperator, BranchPythonOperator
from airflow.operators.bash import BashOperator

from parsing.hooks.db.hook import first_data_saving
from parsing.asnyc_protocol import aiorequest_injection
from parsing.operators.crawling import CrawlingOperator
from parsing.operators.selenium_operators import SeleniumOperator


def status_200_injection(**context: dict[str, Any]) -> list[list[str | dict[str, int]]]:
    data = context["ti"].xcom_pull(task_ids=context["task"].upstream_task_ids)
    loop = asyncio.get_event_loop()
    for i in data:
        loop.run_until_complete(aiorequest_injection(i, 20))


def check_xcom_data(**context):
    ti = context["ti"]
    google_task_output = ti.xcom_pull(task_ids="crawl_google")
    if isinstance(google_task_output, list) and not google_task_output:
        return "google_2nd_task"


with DAG(
    dag_id="Crawling_data_API", start_date=days_ago(5), schedule_interval=None
) as dag:

    start_operator = BashOperator(
        task_id="News_API_start", bash_command="echo crawling start!!", dag=dag
    )

    naver_task = CrawlingOperator(
        task_id="crawl_naver",
        count=10,
        target="BTC",
        site="naver",
        dag=dag,
    )

    daum_task = CrawlingOperator(
        task_id="crawl_daum",
        count=10,
        target="BTC",
        site="daum",
        dag=dag,
    )

    google_task = CrawlingOperator(
        task_id="crawl_google",
        count=10,
        target="BTC",
        site="google",
        dag=dag,
    )

    check_xcom_task = BranchPythonOperator(
        task_id="check_xcom_task",
        python_callable=check_xcom_data,
        provide_context=True,
        dag=dag,
    )

    google_2nd_task = SeleniumOperator(
        task_id="google_2nd_task",
        count=10,
        target="BTC",
        site="google_s",
        dag=dag,
    )

    status = PythonOperator(
        task_id="status_request",
        python_callable=status_200_injection,
        provide_context=True,
        trigger_rule=TriggerRule.ALL_DONE,
        dag=dag,
    )

    saving = PythonOperator(
        task_id="total_data_saving",
        python_callable=first_data_saving,
        provide_context=True,
        trigger_rule=TriggerRule.ALL_DONE,
        dag=dag,
    )

    start_operator >> [naver_task, daum_task, google_task]
    google_task >> check_xcom_task >> google_2nd_task
    [naver_task, daum_task, google_task, google_2nd_task] >> status
    [naver_task, daum_task, google_2nd_task] >> saving
