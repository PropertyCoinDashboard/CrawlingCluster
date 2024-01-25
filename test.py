# """
# 기능 테스트
# """
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


async def main() -> None:
    """
    테스트
    """
    naver_news = NaverNewsParsingDriver(10, "BTC")
    daum_news = DaumNewsParsingDriver(10, "비트코인")

    await asyncio.gather(
        naver_news.get_naver_news_data(),
        daum_news.get_daum_news_data(),
    )


def process_bithum() -> None:
    bithum_parser = BithumSymbolParsingUtility()
    bithum_parser.close_bit_page_and_get_source()


def process_korbit() -> None:
    korbit_parser = KorbitSymbolParsingUtility()
    korbit_parser.korbit_page()


if __name__ == "__main__":
    data = [process_bithum, process_korbit, asyncio.run(main())]
    processes = []

    for p in data:
        process = Process(target=p)
        processes.append(process)
        process.start()

    for pp in processes:
        pp.join()
