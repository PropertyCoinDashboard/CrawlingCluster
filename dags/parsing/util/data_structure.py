import asyncio
import inspect

from parsing.util._typing import (
    UrlDataStructure,
    DataStructure,
    ProcessUrlCollect,
    UrlCollect,
)


def data_structure() -> DataStructure:
    """데이터 묶기 위한 트리 구조 추상화

    Returns:
        DataStructure: {
            1: {1: [], 2: [],3: [], 4: []},
            2: {5: [], 6:[]},
            3: {7: [], 8:[]},
            4: {9: [], 10: []},
        }
    """
    return {
        i: (
            {j: [] for j in range(1, 5)}
            if i == 1
            else (
                {j: [] for j in range(5, 7)}
                if i == 2
                else (
                    {j: [] for j in range(7, 9)}
                    if i == 3
                    else {j: [] for j in range(9, 11)}
                )
            )
        )
        for i in range(1, 5)
    }


def indstrict(page: ProcessUrlCollect) -> UrlDataStructure:
    """

    Args:
        page (ProcessUrlCollect): 각 웹페이지에서 selenium을 이용해서 URL 긁어옴
    Returns:
        UrlDataStructure:
        - \n {
            1: {1: [url 대상들], 2: [url 대상들],3: [url 대상들], 4: [url 대상들]},
            2: {5: [url 대상들], 6:[url 대상들]},
            3: {7: [url 대상들], 8:[url 대상들]},
            4: {9: [url 대상들], 10: [url 대상들]},
        }

    """
    data: DataStructure = data_structure()
    count = 1

    # 요소가 들어올때마다 머금고 있어야함
    url: UrlCollect = page()
    if inspect.iscoroutine(url):
        url = asyncio.run(url)

    while len(url) > 0:
        url_data: list[str] = url.popleft()
        if count >= 9:
            first = 4
        elif count >= 7:
            first = 3
        elif count >= 5:
            first = 2
        else:
            first = 1

        if url_data not in data[first][count]:
            data[first][count] = url_data

        count += 1

    return data
