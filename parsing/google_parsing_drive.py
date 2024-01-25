"""
Google Crawling Parsing Drive
"""

from bs4 import BeautifulSoup
from parsing.selenium_parsing import PageUtilityDriver


class GoogleNewsCrawlingParsingDrive(PageUtilityDriver):
    """
    Google News Parsing Drive

    Args:
        GoogleUtilityDriver (str): _description_
    """

    def __init__(self, url: str) -> None:
        super().__init__(url="https://www.google.com")
