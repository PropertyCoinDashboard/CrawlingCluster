from airflow.providers.mysql.hooks.mysql import MySqlHook


def connection_hook(url: str):
    query = f'INSERT INTO dash.log(url) VALUES ("{url}")'
    MySqlHook(query)
