"""
Google Crawling Parsing Drive
"""
import re
from bs4 import BeautifulSoup


class GoogleNewsCrawlingParsingDrive:
    """
    Google News Parsing Drive

    Args:
        GoogleUtilityDriver (str): _description_
    """

    def news_info_collect(self, html_source: str):
        bs = BeautifulSoup(html_source, "lxml")
        for div_1 in bs.find_all("div", {"data-hveid": re.compile(r"CA|QHw")}):
            for div_2 in div_1.find_all("div", {"class": re.compile(r"SoaBEf")}):
                for a_tag in div_2.find_all("a"):
                    print(a_tag["href"])
