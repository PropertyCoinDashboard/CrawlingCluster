"""
기능 테스트
"""

import asyncio
from airflow import DAG
from airflow.utils.dates import days_ago
from airflow.operators.python import PythonOperator
from airflow.operators.bash import BashOperator


from parsing.naver_daum_news_api import (
    NaverNewsParsingDriver,
    DaumNewsParsingDriver,
)
from parsing.selenium_parsing import (
    KorbitSymbolParsingUtility,
    BithumSymbolParsingUtility,
)
from parsing.selenium_parsing import (
    GoogleMovingElementsLocation,
    BingMovingElementLocation,
)


async def main(count: int, target: str) -> None:
    """
    테스트
    """
    await asyncio.gather(
        NaverNewsParsingDriver(count, target).get_naver_news_data(),
        DaumNewsParsingDriver(count, target).get_daum_news_data(),
    )


def process_bithum() -> None:
    BithumSymbolParsingUtility().close_bit_page_and_get_source()


def process_korbit() -> None:
    KorbitSymbolParsingUtility().korbit_page()


def process_google() -> None:
    GoogleMovingElementsLocation("비트코인", 5).search_box()


def process_bing() -> None:
    BingMovingElementLocation("비트코인", 5).repeat_scroll()


with DAG(
    dag_id="Crawling_data_injectional", start_date=days_ago(5), schedule_interval=None
) as dag:

    start_operator = BashOperator(
        task_id="News_API_start", bash_command="echo crawling start!!"
    )

    naver_daum_api_operator = PythonOperator(
        task_id="get_news_api",
        python_callable=main,
        op_args=[10, "BTC"],
        dag=dag,
    )

    end_operator = BashOperator(
        task_id="News_API_end", bash_command="echo end complete!!"
    )

    start_operator >> naver_daum_api_operator >> end_operator
