# """
# 기능 테스트
# Airflow 발전시키기
# """


import asyncio
import tracemalloc
from typing import Coroutine
from collections import deque
from concurrent.futures import ThreadPoolExecutor, as_completed

from parsing.config.properties import D_HEADERS
from parsing.util._typing import UrlCollect
from parsing.util.util_parser import (
    deep_dive_search,
    AsyncRequestAcquisitionHTML as ARAH,
)
from parsing.nd_paring_driver import DaumNewsParsingDriver
from parsing.selenium_parsing import (
    GoogleMovingElementsLocation,
    BingMovingElementLocation,
)

tracemalloc.start()

# 데이터 적재 하기 위한 추상화
ready_queue = deque()
scheduler_queue = deque()
not_request_queue = deque()


def process_bing(target: str, count: int) -> UrlCollect:
    return BingMovingElementLocation(target, count).repeat_scroll()


def process_google(target: str, count: int) -> UrlCollect:
    return GoogleMovingElementsLocation(target, count).search_box()


async def process_daum(target: str, count: int) -> UrlCollect:
    news_search = DaumNewsParsingDriver(D_HEADERS, target, count)

    # 비동기로 네이버와 카카오 뉴스 URL 가져오기
    daum_news_urls_task = await news_search.extract_news_urls()
    return daum_news_urls_task


async def url_classifier(url: str, status: int) -> None:
    match status:
        case 200:
            ready_queue.append(url)
        case _:
            not_request_queue.append({status: url})


async def aiorequest_injection(start: UrlCollect, batch_size: int) -> None:
    while start:
        node: list[str] = start.popleft()
        if len(node) > 0:
            print(f"묶음 처리 진행합니다 --> {len(node)}개 진행합니다 ")
            for count in range(0, len(node), batch_size):
                batch: list[str] = node[count : count + batch_size]

                tasks: list[Coroutine[tuple[str, int]]] = [
                    ARAH.asnyc_request(url) for url in batch
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


with ThreadPoolExecutor(3) as poll:
    task = [
        poll.submit(deep_dive_search, process, "BTC", 2, objection)
        for process, objection in zip(
            (process_google, process_bing, process_daum), ("google", "bing", "daum")
        )
    ]

    for data in as_completed(task):
        asyncio.run(aiorequest_injection(data.result(), 20))


print(len(ready_queue))
