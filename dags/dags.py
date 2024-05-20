"""
기능 테스트
Airflow 발전시키기
"""

import aiohttp

import asyncio
import tracemalloc
from typing import Coroutine
from collections import deque
from parsing.util.util_parser import deep_dive_search
from parsing.util._typing import UrlCollect
from concurrent.futures import ThreadPoolExecutor, as_completed
from parsing.selenium_parsing import (
    GoogleMovingElementsLocation,
    BingMovingElementLocation,
)


tracemalloc.start()
ready_queue = deque()
scheduler_queue = deque()
not_request_queue = deque()


# 데이터 적재 하기 위한 추상화


async def url_classifier(url: str, status: int) -> None:
    match status:
        case 200:
            ready_queue.append(url)
        case _:
            not_request_queue.append({status: url})


async def fetch_status(url: str) -> tuple[str, int]:
    connector = aiohttp.TCPConnector()
    async with aiohttp.ClientSession(connector=connector, trust_env=True) as session:
        async with session.get(url) as response:
            await asyncio.sleep(0.25)
            if response.status == 200:
                return url, response.status
            else:
                return url, response.status


async def aiorequest_injection(start: UrlCollect, batch_size: int) -> None:
    while start:
        node: list[str] = start.popleft()
        if len(node) > 0:
            print(f"묶음 처리 진행합니다 --> {len(node)}개 진행합니다 ")
            for count in range(0, len(node), batch_size):
                batch: list[str] = node[count : count + batch_size]

                tasks: list[Coroutine[tuple[str, int]]] = [
                    fetch_status(url) for url in batch
                ]
                results: list[tuple[str, int]] = await asyncio.gather(
                    *tasks, return_exceptions=True
                )

                for url_collect in results:
                    if isinstance(url_collect, tuple):
                        url, status = url_collect
                        await url_classifier(url, status)
                    else:
                        print(f"Type 불일치: {url_collect}")


def process_bing(target: str, count: int) -> UrlCollect:
    return BingMovingElementLocation(target, count).repeat_scroll()


def process_google(target: str, count: int) -> UrlCollect:
    return GoogleMovingElementsLocation(target, count).search_box()


with ThreadPoolExecutor(2) as poll:
    task = [
        poll.submit(deep_dive_search, process_google, "BTC", 10, "google"),
        poll.submit(deep_dive_search, process_bing, "BTC", 10, "bing"),
    ]

    for data in as_completed(task):
        asyncio.run(aiorequest_injection(data.result(), 20))


print(len(ready_queue))
print(len(not_request_queue))
