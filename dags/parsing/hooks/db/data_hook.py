from parsing.util.search import AsyncWebCrawler
import asyncio


def data_list_change(**context) -> list[str]:
    url = context["ti"].xcom_pull(key="return_value")
    data_compre: list[str] = [str(*url[i]) for i in range(len(url))]
    return data_compre


async def deep_crawling_run(**context) -> dict[str, set[str]]:
    url = context["ti"].xcom_pull(key="return_value")
    data = [await AsyncWebCrawler(i, 1, 1).run() for i in url]

    context["ti"].xcom_push(key="asnyc_deep", value=data)


def preprocessing(**context) -> list[list[str]]:
    url = context["ti"].xcom_pull(key="asnyc_deep")
    return [first_dict[second] for first_dict in url for second in first_dict]
