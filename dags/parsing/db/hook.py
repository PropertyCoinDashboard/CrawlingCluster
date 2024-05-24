from typing import Any
from airflow.providers.mysql.hooks.mysql import MySqlHook


def connection_hook(url: list[str]) -> None:
    mysql_hook = MySqlHook(mysql_conn_id="airflow-mysql")
    for i in url:
        query = f"INSERT INTO dash.log(url) VALUES ('{i}');"
        mysql_hook.run(query)


def first_data_saving(**context: dict[str, Any]) -> None:
    urls: dict[str, list[list[str]]] = context["ti"].xcom_pull(
        task_ids=context["task"].upstream_task_ids
    )
    for data in urls:
        for i in data:
            connection_hook(i)
