# """
# 기능 테스트
# Airflow 발전시키기
# """

import asyncio
import tracemalloc
from typing import Coroutine
from collections import deque

from parsing.protocol import CrawlingProcess
from parsing.util._typing import UrlCollect, ProcessUrlCollect
from parsing.util.search import AsyncRequestAcquisitionHTML as ARAH, bfs_crawl


tracemalloc.start()

# 데이터 적재 하기 위한 추상화
ready_queue = deque()
scheduler_queue = deque()
not_request_queue = deque()


async def url_classifier(result: list[str | dict[str, int]]) -> None:
    """객체에서 받아온 URL 큐 분류"""
    for url in result:
        if isinstance(url, str):
            ready_queue.append(url)
        elif isinstance(url, dict):
            not_request_queue.append(url)
        else:
            print(f"Type 불일치: {url}")


async def aiorequest_injection(start: UrlCollect, batch_size: int) -> None:
    """starting queue에 담기 위한 시작

    Args:
        start (UrlCollect): 큐
        batch_size (int): 묶어서 처리할 량
    """
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
                await url_classifier(results)


async def main(target: str, count: int) -> list[UrlCollect]:
    """시작점"""
    craw = CrawlingProcess(target, count)
    craw_process: tuple[ProcessUrlCollect] = (
        craw.process_naver(),
        craw.process_daum(),
    )
    data = await asyncio.gather(*craw_process)

    return data


ad = asyncio.run(main("BTC", 2))
for data in ad:
    asyncio.run(aiorequest_injection(data, 20))


while len(ready_queue) > 0:
    data = ready_queue.popleft()
    print(data)

    bfs_crawl(data)
