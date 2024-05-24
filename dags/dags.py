import asyncio

from airflow import DAG
from airflow.utils.dates import days_ago
from airflow.operators.python import PythonOperator
from airflow.operators.bash import BashOperator

from parsing.db.hook import first_data_saving
from parsing.asnyc_protocol import aiorequest_injection
from parsing.operators.crawling import CrawlingOperator


def status_200_injection(**context) -> None:
    data = context["ti"].xcom_pull(task_ids=context["task"].upstream_task_ids)
    loop = asyncio.get_event_loop()
    for i in data:
        loop.run_until_complete(aiorequest_injection(i, 20))


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

    status = PythonOperator(
        task_id="status_request",
        python_callable=status_200_injection,
        provide_context=True,
        dag=dag,
    )

    saving = PythonOperator(
        task_id="mysql_data_saving",
        python_callable=first_data_saving,
        provide_context=True,
        dag=dag,
    )

    start_operator >> [naver_task, daum_task] >> saving
    [naver_task, daum_task] >> status
