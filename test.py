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
from parsing.selenium_parsing import GoogleMovingElementsLocation


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
    GoogleMovingElementsLocation("비트코인").search_box()


if __name__ == "__main__":
    data = [process_bithum, process_korbit, process_google, asyncio.run(main())]
    processes = []

    for p in data:
        process = Process(target=p)
        processes.append(process)
        process.start()

    for pp in processes:
        pp.join()
