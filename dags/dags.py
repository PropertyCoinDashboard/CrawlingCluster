"""
기능 테스트
Airflow 발전시키기
"""

from parsing.util.util_parser import data_structure
from concurrent.futures import ThreadPoolExecutor, as_completed
from parsing.google_bing_parsing_drive import GoogleNewsCrawlingParsingDrive


def indstrict(url_element: list[str]):
    data = data_structure()
    count = 0
    for _ in range(1, 11):
        count += 1
        if count >= 9:
            first = 4
        elif count >= 7:
            first = 3
        elif count >= 5:
            first = 2
        else:
            first = 1

        if url_element not in data[first][count]:
            data[first][count] = url_element
    print(data)
    return data


def process_google(target: str, count: int) -> list[str]:
    return GoogleNewsCrawlingParsingDrive(target, count).saerch_start()


# def process_bing(target: str, count: int) -> None:
#     BingMovingElementLocation(target, count).repeat_scroll()


indstrict(process_google("BTC", 2))

# with ThreadPoolExecutor(2) as poll:
#     task = [
#         poll.submit(process_google, "BTC", 2),
#         # poll.submit(process_bing, "BTC", 2),
#     ]

#     for data in as_completed(task):
#         print(data.result())
