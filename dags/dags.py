"""
기능 테스트
"""

from concurrent.futures import ThreadPoolExecutor, as_completed
from parsing.selenium_parsing import (
    GoogleMovingElementsLocation,
    BingMovingElementLocation,
)


def process_google(target: str, count: int) -> None:
    GoogleMovingElementsLocation(target, count).search_box()


def process_bing(target: str, count: int) -> None:
    BingMovingElementLocation(target, count).repeat_scroll()


process_google("BTC", 2)

# with ThreadPoolExecutor(2) as poll:
#     task = [
#         poll.submit(process_google, "BTC", 3),
#         poll.submit(process_bing, "BTC", 2),
#     ]

#     for data in as_completed(task):
#         data.result()
