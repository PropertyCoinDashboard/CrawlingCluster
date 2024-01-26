"""
bing Crawling Parsing Drive
"""

from bs4 import BeautifulSoup
from parsing.selenium_parsing import PageUtilityDriver


class BingNewsCrawlingParsingDrive(PageUtilityDriver):
    """
    bing News Parsing Drive

    Args:
        PageUtilityDriver (str): Html str
    """

    def __init__(self) -> None:
        super().__init__(url="https://www.bing.com")
