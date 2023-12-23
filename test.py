"""
기능 테스트
"""
import asyncio
from parsing.selenium_util import NaverNewsParsingDriver, DaumNewsParsingDriver


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


asyncio.run(main())
