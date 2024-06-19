import asyncio
from datetime import datetime, timedelta

from airflow import DAG
from airflow.operators.bash import BashOperator
from airflow.operators.python import PythonOperator
from airflow.sensors.external_task import ExternalTaskSensor
from airflow.providers.mysql.operators.mysql import MySqlOperator
from airflow.utils.task_group import TaskGroup
from airflow.providers.amazon.aws.operators.s3 import S3CreateBucketOperator
from airflow.providers.amazon.aws.sensors.s3 import S3KeySensor
from parsing.drive.naver_parsing_api import NaverNewsParsingDriver
from parsing.operators.crawling import CrawlingOperator
from parsing.hooks.db.hook import DatabaseHandler, Pipeline
from parsing.hooks.db.data_hook import (
    data_list_change,
    deep_crawling_run,
    preprocessing,
    extract_mysql_data_to_s3,
)


db_handler = DatabaseHandler()
pipeline = Pipeline(db_handler)


def response_html(search_keyword: str, count: int) -> dict[str, bool]:
    data = NaverNewsParsingDriver(search_keyword, count).fetch_page_urls()
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


def create_status_task(task_group_name: str, dag: DAG, pipeline: Pipeline) -> TaskGroup:
    with TaskGroup(task_group_name, dag=dag) as group:
        status_requesting = PythonOperator(
            task_id="classifier",
            python_callable=async_process_injection,
            op_kwargs={"process": pipeline.aiorequest_classification},
            dag=dag,
        )

        not_request = PythonOperator(
            task_id="not_request",
            python_callable=async_process_injection,
            op_kwargs={"process": pipeline.not_request_saving},
            dag=dag,
        )

        request_200 = PythonOperator(
            task_id="200_request",
            python_callable=async_process_injection,
            op_kwargs={"process": pipeline.request_saving},
            dag=dag,
        )

        status_requesting >> not_request
        status_requesting >> request_200

    return group


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
    # schedule_interval=timedelta(minutes=10),
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
        count=10,
        target="BTC",
        site="naver",
        dag=dag,
    )

    saving = PythonOperator(
        task_id="saving", python_callable=first_data_saving_task, dag=dag
    )

    create_bucket = S3CreateBucketOperator(
        task_id="s3_bucket_dag_create",
        bucket_name=None,
        aws_conn_id="your_aws_connection_id",
        dag=dag,
    )

    log_saving = PythonOperator(
        task_id="log_saving", python_callable=extract_mysql_data_to_s3, dag=dag
    )

    status_tasks = create_status_task("status_tasks", dag, pipeline)

    # create_bucket_task = S3CreateBucketOperator(
    #     task_id="create_s3_bucket",
    #     bucket_name=s3_bucket_name,
    #     region_name=aws_region_name,
    #     aws_conn_id="aws_default",
    #     create_bucket_config={"LocationConstraint": aws_region_name},
    #     enforce_s3_bucket="no_exists",
    #     dag=dag,
    # )

    # wait_for_s3_key_task = S3KeySensor(
    #     task_id="wait_for_s3_key",
    #     bucket_name=s3_bucket_name,
    #     bucket_key=s3_key,
    #     wildcard_match=False,
    #     timeout=600,
    #     poke_interval=30,
    #     aws_conn_id="aws_default",
    #     dag=dag,
    # )

    (
        response
        >> wait_for_api_response
        >> start_operator
        >> naver
        >> saving
        # >> create_bucket_task
        # >> wait_for_s3_key_task
    )
    naver >> status_tasks


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

    status_tasks = create_status_task("deep_status_tasks", dag, pipeline)

    url_selection >> hooking >> th >> prepro >> status_tasks


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
            dag=dag,
        )

        url_selection >> process_url_data_task

    return dag


dag1 = create_url_status_dag("another_request_check", "not_request_url")
dag2 = create_url_status_dag("200_request_check", "request_url")
