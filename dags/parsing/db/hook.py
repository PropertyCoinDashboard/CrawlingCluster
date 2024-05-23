from airflow.providers.mysql.hooks.mysql import MySqlHook


def connection_hook(url: str) -> None:
    query = f"INSERT INTO dash.log(url) VALUES ('{url}')"
    mysql_hook = MySqlHook(mysql_conn_id="airflow-mysql")
    mysql_hook.run(query)


def first_data_saving(**context) -> None:
    urls = context["ti"].xcom_pull(task_ids=context["task"].upstream_task_ids)
    for data in urls:
        for i in data:
            connection_hook(i)
