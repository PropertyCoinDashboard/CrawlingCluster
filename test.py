# """
# 기능 테스트
# """
import asyncio
from parsing.nd_news_apis.naver_daum import (
    NaverNewsParsingDriver,
    DaumNewsParsingDriver,
)
from multiprocessing import Process
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


def process_bithum():
    bithum_parser = BithumSymbolParsingUtility()
    result = bithum_parser.close_bit_page_and_get_source()
    # Process the result if needed


def process_korbit():
    korbit_parser = KorbitSymbolParsingUtility()
    result = korbit_parser.korbit_page()
    # Process the result if needed


if __name__ == "__main__":
    # Create separate processes for each utility
    asyncio.run(main())

    bithum_process = Process(target=process_bithum)
    korbit_process = Process(target=process_korbit)

    # Start the processes
    bithum_process.start()
    korbit_process.start()

    # Wait for both processes to finish
    bithum_process.join()
    korbit_process.join()
