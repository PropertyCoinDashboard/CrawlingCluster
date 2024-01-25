"""
bing Crawling Parsing Drive
"""

from bs4 import BeautifulSoup
from parsing.selenium_parsing import PageUtilityDriver


class BingNewsCrawlingParsingDrive(PageUtilityDriver):
    """
    Google News Parsing Drive

    Args:
        GoogleUtilityDriver (_type_): _description_
    """

    def __init__(self, url: str) -> None:
        super().__init__(url="https://www.bing.com")
