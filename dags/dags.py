"""
기능 테스트
"""

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
    KorbitSymbolParsingUtility,
    BithumSymbolParsingUtility,
)
from parsing.selenium_parsing import (
    GoogleMovingElementsLocation,
    BingMovingElementLocation,
)


# sql_create_table: str = """
#     CREATE TABLE `log` (
#     `id` int NOT NULL AUTO_INCREMENT,
#     `location` varchar(45) NOT NULL,
#     `title` datetime NOT NULL,
#     `url` varchar(45) NOT NULL,
#     PRIMARY KEY (`id`)
#     ) ENGINE=InnoDB AUTO_INCREMENT=83852 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci
# """

# # MySQL 연결 설정
# mysql_conn_id = "airflow-sql"
# mysql_hook = MySqlHook(mysql_conn_id=mysql_conn_id)


def naver(count: int, target: str) -> None:
    NaverNewsParsingDriver(count, target).get_naver_news_data(),


def daum(count: int, target: str) -> None:
    DaumNewsParsingDriver(count, target).get_daum_news_data(),


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

    end_operator = BashOperator(
        task_id="News_API_end", bash_command="echo end complete!!"
    )

    start_operator >> naver_api_operator >> end_operator
    start_operator >> daum_api_operator >> end_operator
