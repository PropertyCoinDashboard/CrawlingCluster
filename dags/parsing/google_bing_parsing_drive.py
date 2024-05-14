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

    def div_in_class(self, element: BeautifulSoup) -> list[str]:
        """google page 요소 두번째 접근 단계

        <div data-hveid="CA~QHw">
            <div class="SoaBEf"> --> 현 위치 [구글 페이지는 맨 마지막에 SoaBEf sdf 이런식으로 무작위 난수가 되어 있어서 정규표현식 진행]

        Returns:
            list[str]: ["요소들", ~~]
        """
        return element.find_all("div", {"class": re.compile(r"SoaBEf")})

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
        """
        # 첫번쨰 요소 접근  -> <div data-hveid="CA~QHw">
        div_in_data_hveid: list = soup_data(
            html_data=html_source,
            element="div",
            elements={"data-hveid": re.compile(r"CA|QHw")},
            soup=BeautifulSoup(html_source, "lxml"),
        )
        for div_1 in div_in_data_hveid:
            for div_2 in self.div_in_class(div_1):
                for a_tag in self.div_a_tags(div_2):
                    title = self.href_from_text_preprocessing(a_tag.text)[:20]
                    url = a_tag["href"]
                    print(title, url)
                    query = f'INSERT INTO dash.log(location, title, url) VALUES ("Google", "{title}", "{url}")'
                    # mysql_saving_hook(query)


class BingNewsCrawlingParsingDrive:
    """
    bing News Parsing Drive

    """

    def div_in_class(self, element: BeautifulSoup) -> list[str]:
        """bing page 요소 두번째 접근 단계

        <div class="algocore">
            <div class="news-card newsitem cardcommon">  --> 현 위치
        Args:
            element (BeautifulSoup)
        Returns:
            list[str]: ["요소들", ~~]
        """
        return element.find_all("div", {"class": "news-card newsitem cardcommon"})

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
        """시작점

        Args:
            html_source (str): HTML

        """
        # 첫번쨰 요소 접근  -> <div class="algocore">
        div_class_algocore: list = soup_data(
            html_data=html_source,
            element="div",
            elements={"class": "algocore"},
            soup=BeautifulSoup(html_source, "lxml"),
        )
        for div_1 in div_class_algocore:
            for div_2 in self.div_in_class(div_1):
                url = div_2["url"]
                title = self.href_from_text_preprocessing(div_2["data-title"][:20])
                query = f'INSERT INTO dash.log(location, title, url) VALUES ("Bing", "{title}", "{url}")'
                print(url, title)
                # mysql_saving_hook(query)
