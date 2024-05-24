import asyncio

from airflow import DAG
from airflow.utils.dates import days_ago
from airflow.operators.python import PythonOperator
from airflow.operators.bash import BashOperator
from airflow.providers.mysql.hooks.mysql import MySqlHook

from parsing.db.hook import first_data_saving
from parsing.asnyc_protocol import aiorequest_injection
from parsing.protocol import CrawlingProcess

# # # MySQL 연결 설정
mysql_conn_id = "airflow-mysql"
mysql_hook = MySqlHook(mysql_conn_id=mysql_conn_id)


def naver_again(count: int, target: str) -> list[list[str]]:
    loop = asyncio.get_event_loop()
    result = loop.run_until_complete(CrawlingProcess(target, count).process_naver())
    data = [i for i in result]
    return data


def daum_again(count: int, target: str) -> list[list[str]]:
    loop = asyncio.get_event_loop()
    result = loop.run_until_complete(CrawlingProcess(target, count).process_daum())
    data = [i for i in result]
    return data


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

    naver_api_operator = PythonOperator(
        task_id="get_news_api_naver",
        python_callable=naver_again,
        op_args=[10, "BTC"],
        dag=dag,
    )

    daum_api_operator = PythonOperator(
        task_id="get_news_api_daum",
        python_callable=daum_again,
        op_args=[10, "BTC"],
        dag=dag,
    )

    status = PythonOperator(
        task_id="200_status_classifer",
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

    start_operator >> [naver_api_operator, daum_api_operator] >> saving
    [naver_api_operator, daum_api_operator] >> status
