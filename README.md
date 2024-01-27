# CrawlingCluster

## 상속 구조 
![크롤링 설계도 drawio](https://github.com/PropertyCoinDashboard/CrawlingCluster/assets/52487610/743813fc-f611-4455-96a0-e2dcb1bae860)

---

API 끌고온것듯
- Naver
- KaKao

셀레니움 동적 크롤링 대상 
- google
- bing
- Korbit
  - coin symbol 
- Bithumb
  - coin symbol
 

### 실행 (멀티 프로세싱으로 했으나 Airflow로 각각 원하는 키워드에 스케줄링 고려)
- python test.py
```python
"""
기능 테스트
"""
import asyncio
from multiprocessing import Process

from parsing.naver_daum_news_api import (
    NaverNewsParsingDriver,
    DaumNewsParsingDriver,
)
from parsing.selenium_parsing import (
    KorbitSymbolParsingUtility,
    BithumSymbolParsingUtility,
)
from parsing.selenium_parsing import (
    GoogleMovingElementsLocation,
    BingMovingElementLocation,
)


async def main() -> None:
    """
    테스트
    """
    await asyncio.gather(
        NaverNewsParsingDriver(10, "BTC").get_naver_news_data(),
        DaumNewsParsingDriver(10, "비트코인").get_daum_news_data(),
    )


def process_bithum() -> None:
    BithumSymbolParsingUtility().close_bit_page_and_get_source()


def process_korbit() -> None:
    KorbitSymbolParsingUtility().korbit_page()


def process_google() -> None:
    GoogleMovingElementsLocation("비트코인", 5).search_box()


def process_bing() -> None:
    BingMovingElementLocation("비트코인", 5).repeat_scroll()


if __name__ == "__main__":
    data = [
        process_bithum,
        process_korbit,
        process_google,
        process_bing,
        asyncio.run(main()),
    ]
    processes = []

    for p in data:
        process = Process(target=p)
        processes.append(process)
        process.start()

    for pp in processes:
        pp.join()
```
