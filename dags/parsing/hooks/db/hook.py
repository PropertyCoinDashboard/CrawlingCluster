# from typing import Any
# from airflow.providers.mysql.hooks.mysql import MySqlHook

# mysql_hook = MySqlHook(mysql_conn_id="airflow-mysql")


# def not_ready_status(url: dict[str, int]) -> None:
#     for url, status in url.items():
#         query = f"INSERT INTO dash.status_another(status_code, url) VALUES ('{status}', '{url}');"
#         mysql_hook.run(query)


# # 데이터 적재 하기 위한 추상화
# def ready_request_status(url: str) -> None:
#     query = f"INSERT INTO dash.status_200(url) VALUES ('{url}');"
#     mysql_hook.run(query)


# def connection_hook(url: list[str]) -> None:
#     for i in url:
#         query = f"INSERT INTO dash.log(url) VALUES ('{i}');"
#         mysql_hook.run(query)


# def first_data_saving(**context: dict[str, Any]) -> None:
#     urls: dict[str, list[list[str]]] = context["ti"].xcom_pull(
#         task_ids=context["task"].upstream_task_ids
#     )
#     for data in urls:
#         for i in data:
#             connection_hook(i)


# async def url_classifier(**context: list[str | dict[str, int]]) -> None:
#     """객체에서 받아온 URL 큐 분류"""
#     urls: dict[str, list[list[str]]] = context["ti"].xcom_pull(
#         task_ids=context["task"].upstream_task_ids
#     )
#     for data in urls:
#         for i in data:
#             if isinstance(i, str):
#                 ready_request_status(i)
#             elif isinstance(i, dict):
#                 not_ready_status(i)
#             else:
#                 print(f"Type 불일치: {i}")
