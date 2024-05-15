"""
Google Crawling Parsing Drive
"""

import re
from pathlib import Path
from bs4 import BeautifulSoup
from parsing.util.util_parser import soup_data

path_location = Path(__file__).parent.parent.parent


class GoogleNewsCrawlingParsingDrive:
    """
    Google News Parsing Drive

    """

    def __init__(self) -> None:
        self.processed_urls = set()  # 이미 처리된 URL을 추적하기 위한 세트

    def div_in_class(self, element: BeautifulSoup) -> list[str]:
        """google page 요소 두번째 접근 단계

        <div data-hveid="CA~QHw">
            <div class="MjjYud"> --> 현 위치 [구글 페이지는 맨 마지막에 MjjYud 전체 묶임]

        Returns:
            list[str]: ["요소들", ~~]
        """
        return element.find_all("div", {"class": "MjjYud"})

    def div_a_tags(self, div_2: BeautifulSoup) -> list[str]:
        """google page 요소 세번째 접근 단계

        <div data-hveid="CA~QHw">
            <div class="SoaBEf">
                <div> ~
                    <a jsname="YKoRaf"> --> 현위치

        Returns:
            list[str]: ["요소들", ~~]
        """
        return div_2.find_all("a", {"jsname": "YKoRaf"})

    def href_from_a_tag(self, a_tag: BeautifulSoup) -> str:
        """URL 뽑아내기

        Returns:
            str: [URL, ~~]
        """
        return a_tag.get("href")

    def href_from_text_preprocessing(self, text: str) -> str:
        """텍스트 전처리

        Args:
            text (str): URL title 및 시간
                - ex) 어쩌구 저쩌구...12시간

        Returns:
            str: 특수문자 및 시간제거
                - ex) 어쩌구 저쩌구
        """
        return re.sub(r"\b\d+시간 전\b|\.{2,}|[^\w\s]", "", text)

    def news_info_collect(self, html_source: str) -> None:
        """요소 추출 시작점

        Args:
            html_source (str): HTML
            jsmodel="ROaKxe"
            jsmodel="ROaKxe"
            MjjYud -> 10개 하지만 없는것도 있음
        """
        # 첫번쨰 요소 접근  -> <div data-hveid="CA~QHw">
        div_in_data_hveid: list = soup_data(
            html_data=html_source,
            element="div",
            elements={
                "data-hveid": re.compile(r"CA|QHw|CA[0-9a-zA-Z]+|CB[0-9a-zA-Z]+")
            },
            soup=BeautifulSoup(html_source, "lxml"),
        )
        for div_1 in div_in_data_hveid:
            for div_2 in self.div_in_class(div_1):
                for a_tag in self.div_a_tags(div_2):
                    url = self.href_from_a_tag(a_tag)
                    title = self.href_from_text_preprocessing(a_tag.text)[:20]
                    print(url, title)


class BingNewsCrawlingParsingDrive:
    """
    bing News Parsing Drive

    """

    def div_in_class(self, element: BeautifulSoup, target: str) -> list[str]:
        """bing page 요소 두번째 접근 단계

        <div class="algocore">
            <div class="news-card newsitem cardcommon">  --> 현 위치
        <div class="nwscnt">
            <div class="newscard vr">
            두가지 버전 존재
        Args:
            element (BeautifulSoup)
        Returns:
            list[str]: ["요소들", ~~]
        """
        return element.find_all("div", {"class": target})

    def href_from_text_preprocessing(self, text: str) -> str:
        """텍스트 전처리

        Args:
            text (str): URL title 및 시간
                - ex) 어쩌구 저쩌구...12시간

        Returns:
            str: 특수문자 및 시간제거
                - ex) 어쩌구 저쩌구
        """
        return re.sub(r"\b\d+시간 전\b|\.{2,}|[^\w\s]", "", text)

    # fmt: off
    def detection_element(
        self, html_source: str, *element: tuple[str]
    ) -> tuple[str, str]:
        pattern = r'class="([^"]+)"'
        class_values = set(element for element in re.findall(pattern, html_source))
        data = tuple(elem for elem in element if elem in class_values)
        return data

    def news_info_collect(self, html_source: str) -> None:
        """시작점

        Args:
            html_source (str): HTML

        """
        # 첫번쨰 요소 접근  -> <div class="algocore"> or nwscnt
        detect: tuple[str, str] = self.detection_element(
            html_source,
            "nwscnt",
            "newscard vr",
            "algocore",
            "news-card newsitem cardcommon",
        )
        div_class_algocore: list = soup_data(
            html_data=html_source,
            element="div",
            elements={"class": detect[0]},
            soup=BeautifulSoup(html_source, "lxml"),
        )

        for div_1 in div_class_algocore:
            for div_2 in self.div_in_class(div_1, detect[1]):
                url = div_2["url"]
                title = self.href_from_text_preprocessing(div_2["data-title"][:20])
                query = f'INSERT INTO dash.log(location, title, url) VALUES ("Bing", "{title}", "{url}")'
                print(url, title)
                # mysql_saving_hook(query)
