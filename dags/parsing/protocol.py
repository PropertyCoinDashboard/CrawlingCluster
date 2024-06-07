from parsing.config.properties import D_HEADERS
from parsing.util._typing import UrlCollect
from parsing.drive.nd_paring_driver import (
    DaumNewsParsingDriver,
    NaverNewsParsingDriver,
    GoogleNewsParsingDriver,
)
from parsing.drive.selenium_parsing import (
    GoogleMovingElementsLocation,
    BingMovingElementLocation,
)


class CrawlingProcess:
    """프로세스 모음집"""

    def __init__(self, target: str, count: int) -> None:
        """긁어올 생성자

        Args:
            target (str): 긁어올 타겟
            count (int): 긁어올 횟수
        """
        self.target = target
        self.count = count

    def process_bing_selenium(self) -> UrlCollect:
        """bing 크롤링"""
        return BingMovingElementLocation(self.target, self.count).repeat_scroll()

    def process_google_selenium(self) -> UrlCollect:
        """google 크롤링"""
        return GoogleMovingElementsLocation(self.target, self.count).search_box()

    # fmt: off
    # async def process_daum(self) -> UrlCollect:
    #     """daum 크롤링"""
    #     return await DaumNewsParsingDriver(self.target, self.count, D_HEADERS).extract_news_urls()

    async def process_naver(self) -> UrlCollect:
        """naver 크롤링"""
        return await NaverNewsParsingDriver(self.target, self.count).extract_news_urls()

    async def process_google(self) -> UrlCollect:
        return await GoogleNewsParsingDriver(self.target, self.count).extract_news_urls()
