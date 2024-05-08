"""
기능 테스트
"""

from typing import Any
import time

from airflow import DAG
from airflow.utils.dates import days_ago
from airflow.operators.python import PythonOperator
from airflow.operators.bash import BashOperator
from airflow.providers.mysql.hooks.mysql import MySqlHook

from parsing.naver_daum_news_api import (
    NaverNewsParsingDriver,
    DaumNewsParsingDriver,
)

from parsing.selenium_parsing import (
    GoogleMovingElementsLocation,
    BingMovingElementLocation,
)


# # MySQL 연결 설정
mysql_conn_id = "airflow-mysql"
mysql_hook = MySqlHook(mysql_conn_id=mysql_conn_id)


def naver(count: int, target: str) -> None:
    NaverNewsParsingDriver(count, target).get_naver_news_data(),


def daum(count: int, target: str) -> None:
    DaumNewsParsingDriver(count, target).get_daum_news_data(),


def process_google(**kwargs) -> Any:
    return GoogleMovingElementsLocation(kwargs["target"], kwargs["count"]).search_box()


def process_bing(**kwargs) -> Any:
    return BingMovingElementLocation(kwargs["target"], kwargs["count"]).repeat_scroll()


def driver_sleep():
    time.sleep(30)


with DAG(
    dag_id="Crawling_data_API", start_date=days_ago(5), schedule_interval=None
) as dag:

    start_operator = BashOperator(
        task_id="News_API_start", bash_command="echo crawling start!!", dag=dag
    )

    naver_api_operator = PythonOperator(
        task_id="get_news_api_naver",
        python_callable=naver,
        op_args=[10, "BTC"],
        dag=dag,
    )

    daum_api_operator = PythonOperator(
        task_id="get_news_api_daum",
        python_callable=daum,
        op_args=[10, "BTC"],
        dag=dag,
    )

    saving_operator = BashOperator(
        task_id="News_API_saving", bash_command="echo saving complete!!", dag=dag
    )

    end_operator = BashOperator(
        task_id="News_API_end", bash_command="echo end complete!!", dag=dag
    )

    start_operator >> naver_api_operator >> saving_operator >> end_operator
    start_operator >> daum_api_operator >> saving_operator >> end_operator


with DAG(
    dag_id="Crawling_data_Selenium", start_date=days_ago(5), schedule_interval=None
) as dag:

    start_operator = BashOperator(
        task_id="News_API_start", bash_command="echo crawling start!!", dag=dag
    )

    google_sel_operator = PythonOperator(
        task_id="get_news_api_google",
        python_callable=process_google,
        op_kwargs={"target": "BTC", "count": 2},
        dag=dag,
    )

    sleep_driver_operator = PythonOperator(
        task_id="driver_sleep", python_callable=driver_sleep, dag=dag
    )

    bing_sel_operator = PythonOperator(
        task_id="get_news_api_bing",
        python_callable=process_bing,
        op_kwargs={"target": "BTC", "count": 2},
        dag=dag,
    )

    saving_operator = BashOperator(
        task_id="News_API_saving", bash_command="echo saving complete!!", dag=dag
    )

    end_operator = BashOperator(
        task_id="News_API_end", bash_command="echo end complete!!", dag=dag
    )

    (
        start_operator
        >> google_sel_operator
        >> sleep_driver_operator
        >> bing_sel_operator
        >> saving_operator
        >> end_operator
    )
