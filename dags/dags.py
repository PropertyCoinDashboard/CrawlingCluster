import asyncio
import json
from parsing.util._typing import UrlCollect

from airflow import DAG
from airflow.utils.dates import days_ago
from airflow.operators.python import PythonOperator
from airflow.operators.bash import BashOperator
from airflow.providers.mysql.hooks.mysql import MySqlHook

from parsing.db.hook import first_data_saving
from parsing.protocol import CrawlingProcess

# # # MySQL 연결 설정
mysql_conn_id = "airflow-mysql"
mysql_hook = MySqlHook(mysql_conn_id=mysql_conn_id)


def naver_again(count: int, target: str) -> UrlCollect:
    loop = asyncio.get_event_loop()
    result = loop.run_until_complete(CrawlingProcess(target, count).process_naver())
    serialization = json.dumps(list(result))
    return serialization


def daum_again(count: int, target: str) -> UrlCollect:
    loop = asyncio.get_event_loop()
    result = loop.run_until_complete(CrawlingProcess(target, count).process_daum())
    serialization = json.dumps(list(result))
    return serialization


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

    saving = PythonOperator(
        task_id="mysql_data_saving",
        python_callable=first_data_saving,
        provide_context=True,
        dag=dag,
    )

    start_operator >> [naver_api_operator, daum_api_operator] >> saving
