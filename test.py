from parsing.selenium_util import NaverNewsParsingDriver, DaumNewsParsingDriver
import asyncio


async def main():
    naver_news = NaverNewsParsingDriver(10, "python")
    daum_news = DaumNewsParsingDriver(10, "python")

    await asyncio.gather(
        naver_news.get_naver_news_data(),
        daum_news.get_daum_news_data(),
    )


asyncio.run(main())
