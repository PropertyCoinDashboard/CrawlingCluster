"""
Google Crawling Parsing Drive
"""
import re
from bs4 import BeautifulSoup
from parsing.util.util_parser import soup_data


class GoogleNewsCrawlingParsingDrive:
    """
    Google News Parsing Drive

    """

    def div_in_class(self, element: BeautifulSoup) -> list[str]:
        return element.find_all("div", {"class": re.compile(r"SoaBEf")})

    def div_a_tags(self, div_2: BeautifulSoup) -> list[str]:
        return div_2.find_all("a")

    def href_from_a_tag(self, a_tag: BeautifulSoup) -> str:
        return a_tag.get("href")

    def href_from_text_preprocessing(self, text: str) -> str:
        return re.sub(r"\b\d+시간 전\b|\.{2,}\b", "", text)

    def news_info_collect(self, html_source: str) -> None:
        div_in_data_hveid: list = soup_data(
            html_data=html_source,
            element="div",
            elements={"data-hveid": re.compile(r"CA|QHw")},
            soup=BeautifulSoup(html_source, "lxml"),
        )

        for div_1 in div_in_data_hveid:
            for div_2 in self.div_in_class(div_1):
                for a_tag in self.div_a_tags(div_2):
                    print(a_tag["href"], self.href_from_text_preprocessing(a_tag.text))


class BingNewsCrawlingParsingDrive:
    """
    bing News Parsing Drive

    """

    def div_in_class(self, element: BeautifulSoup) -> list[str]:
        return element.find_all("div", {"class": "news-card newsitem cardcommon"})

    def news_info_collect(self, html_source: str) -> None:
        div_class_algocore: list = soup_data(
            html_data=html_source,
            element="div",
            elements={"class": "algocore"},
            soup=BeautifulSoup(html_source, "lxml"),
        )
        for div_1 in div_class_algocore:
            for div_2 in self.div_in_class(div_1):
                print(div_2["url"], div_2["data-title"])
