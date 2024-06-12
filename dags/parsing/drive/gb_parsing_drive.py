"""
Google Crawling Parsing Drive
"""

import re
from bs4 import BeautifulSoup
from parsing.util.parser_util import soup_data, href_from_a_tag

HTML = str


class DaumNewsCrawlingParsingDrive:
    """Daum 뉴스 크롤링 파싱 드라이버"""

    def ul_in_class(self, element: BeautifulSoup) -> list[str]:
        """
        Args:
            <ul class="c-list-basic"> <---- 탐색 지점
                <li data-docid=26이후 무작위 난수>   <---- 리턴값
                <li data-docid=26이후 무작위 난수>
                <li data-docid=26이후 무작위 난수>
            </ul>
        Returns:
            list[str]: 클래스가 'c-list-basic'인 'ul' 요소들의 리스트.
        """
        return element.find_all("ul", {"class": "c-list-basic"})

    def li_in_data_docid(self, element: BeautifulSoup) -> list[str]:
        """
        Args:
            <li data-docid=26이후 무작위 난수>
        Returns:
            list[str]: 정규식 패턴과 일치하는 'data-docid' 속성을 가진 'li' 요소들의 리스트.
        """
        match = re.compile(r"^26.*")
        return element.find_all("li", {"data-docid": match})

    def strong_in_class(self, element: BeautifulSoup) -> list[str]:
        """
        Args:
            <li data-docid=26이후 무작위 난수>
                <div class="item-title">
                    <strong class=tit-g clamp-g>  <----- 탐색 지점
                        <a href=URL></a> <----- 리턴값
                    </strong>
                </div>
            </li>

        Returns:
            list[str]: 클래스가 'tit-g clamp-g'인 'strong' 요소들의 리스트.
        """
        return element.find_all("strong", {"class": "tit-g clamp-g"})

    def spen_in_class(self, element: BeautifulSoup) -> list[str]:
        """
        Args:
            <li data-docid=26이후 무작위 난수>
                <div class="item-contents">
                    <span class="gem-subinfo"> <---- 탐색 지점
                        <span class="txt_info"> </span> <--- 리턴값
                    </span>
                </div>
            </li>

        Returns:
            list[str]: 클래스가 'gem-subinfo'인 'span' 요소들의 리스트.
        """
        return element.find_all("span", {"class": "gem-subinfo"})

    def news_info_collect(self, html_source: str) -> list[dict[str, str]]:
        """HTML 소스에서 요소 추출을 시작함.

        Args:
            html_source (str): HTML 소스 코드 문자열.
        Returns:
            list[dict[str, str, str]]: 각 뉴스 항목에 대한 'url', 'date', 'title'을 포함하는 딕셔너리 리스트.
        """
        div_in_data_hveid: list[HTML] = soup_data(
            html_data=html_source,
            element="ul",
            elements={"class": "c-list-basic"},
            soup=BeautifulSoup(html_source, "lxml"),
        )

        li_in_data_docid_cache: list[list[str]] = [
            self.li_in_data_docid(div_1) for div_1 in div_in_data_hveid
        ]

        data_list = []
        for div_2_list in li_in_data_docid_cache:
            for div_2 in div_2_list:
                # 'strong' 태그와 'span' 태그를 한 번에 추출
                strong_tags = self.strong_in_class(div_2)
                spen_tags = self.spen_in_class(div_2)

                # 링크, 날짜, 텍스트를 동시에 추출
                for strong_tag, spen_tag in zip(strong_tags, spen_tags):
                    links = (
                        a_tag["href"] for a_tag in strong_tag.find_all("a", href=True)
                    )

                    texts = (
                        a_tag.text.replace(" ", "").strip()
                        for a_tag in strong_tag.find_all("a")
                    )

                    dates = (
                        spen_tags.text
                        for spen_tags in spen_tag.find_all(
                            "span", {"class": "txt_info"}
                        )
                    )
                    # 링크, 날짜, 텍스트를 결합하여 딕셔너리로 만들고 data_list에 추가
                    data_list.extend(
                        {"url": link, "date": date, "title": text}
                        for link, date, text in zip(links, dates, texts)
                    )

        return data_list


class GoogleNewsCrawlingParsingDrive:
    """
    Google News Parsing Drive

    """

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

    def news_info_collect(self, html_source: str) -> list[str]:
        """요소 추출 시작점

        Args:
            html_source (str): HTML
        """
        # 첫번쨰 요소 접근  -> <div data-hveid="CA~QHw">
        # 요소별 무작위 난수이므로 정규표현식 사용
        element = []
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
                    url = href_from_a_tag(a_tag, "href")
                    # title = href_from_text_preprocessing(a_tag.text)[:20]
                    element.append(url)
                return element


class BingNewsCrawlingParsingDrive:
    """
    bing News Parsing Drive

    """

    def div_in_class(self, element: BeautifulSoup, target: str) -> list[str]:
        """bing page 요소 두번째 접근 단계

        Args:
            element (BeautifulSoup)
        Returns:
            list[str]: ["요소들", ~~]
        """
        return element.find_all("div", {"class": target})

    def detection_element(self, html_source: str, *element: str) -> tuple[str]:
        """Bing HTML element 요소 추출하기

        Args:
            html_source (str) : HTML
            element (tuple[str]) : HTML에 div new를 담기고 있는 후보들
                - ex)
                \n
                <div class="algocore">
                    <div class="news-card newsitem cardcommon">
                        뉴스
                    </div>
                </div>

                <div class="nwscnt">
                    <div class="newscard vr">
                        뉴스
                    </div>
                </div<

        Return: (tuple[str, str])
            - 파악된 요소들
        """
        pattern = r'class="([^"]+)"'
        class_values: set[str] = set(
            element for element in re.findall(pattern, html_source)
        )
        data: tuple[str, ...] = tuple(elem for elem in element if elem in class_values)
        return data

    def news_info_collect(self, html_source: str) -> list[str]:
        """시작점

        Args:
            html_source (str): HTML

        """
        # 첫번쨰 요소 접근  -> <div class="algocore"> or nwscnt
        # 요소 필터링 하여 확인 되는 요소만 크롤링할 수 있게 행동 제약
        detect: tuple[str] = self.detection_element(
            html_source,
            "nwscnt",
            "newscard vr",
            "algocore",
            "news-card newsitem cardcommon",
        )
        print(f"Bing 다음요소로 수집 진행합니다 --> {detect}")
        div_class_algocore: list[str] = soup_data(
            html_data=html_source,
            element="div",
            elements={"class": detect[0]},
            soup=BeautifulSoup(html_source, "lxml"),
        )

        data = [
            href_from_a_tag(div_2, "url")
            for div_1 in div_class_algocore
            for div_2 in self.div_in_class(div_1, detect[1])
        ]

        return data
