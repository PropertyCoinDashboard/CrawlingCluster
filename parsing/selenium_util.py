"""
crawling selenium 
"""

import time
import configparser
from pathlib import Path
from typing import Any, Coroutine
from abc import ABCMeta, abstractmethod


import aiohttp
import requests
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait


from parsing.web_parser import CoinSymbolParsingDriver
from parsing.schema.create_log import log
from parsing.schema.util_parser import csv_saving
from parsing.schema.xpath_location import USERAGENT, WAIT_TIME, BITHUM_POPUP_BUTTON


# 부모 경로
path_location = Path(__file__).parent.parent

# key_parser
parser = configparser.ConfigParser()
parser.read(f"{path_location}/config/url.conf")

naver_id: str = parser.get("naver", "X-Naver-Client-Id")
naver_secret: str = parser.get("naver", "X-Naver-Client-Secret")
naver_url: str = parser.get("naver", "NAVER_URL")

daum_auth: str = parser.get("daum", "Authorization")
daum_url: str = parser.get("daum", "DAUM_URL")


# 크롬 옵션 설정
option_chrome = webdriver.ChromeOptions()
option_chrome.add_argument("headless")
option_chrome.add_argument("disable-gpu")
option_chrome.add_argument("disable-infobars")
option_chrome.add_argument("--disable-extensions")
option_chrome.add_argument("user-agent=" + USERAGENT)


prefs: dict[str, dict[str, int]] = {
    "profile.default_content_setting_values": {
        "cookies": 2,
        "images": 2,
        "plugins": 2,
        "popups": 2,
        "geolocation": 2,
        "notifications": 2,
        "auto_select_certificate": 2,
        "fullscreen": 2,
        "mouselock": 2,
        "mixed_script": 2,
        "media_stream": 2,
        "media_stream_mic": 2,
        "media_stream_camera": 2,
        "protocol_handlers": 2,
        "ppapi_broker": 2,
        "automatic_downloads": 2,
        "midi_sysex": 2,
        "push_messaging": 2,
        "ssl_cert_decisions": 2,
        "metro_switch_to_desktop": 2,
        "protected_media_identifier": 2,
        "app_banner": 2,
        "site_engagement": 2,
        "durable_storage": 2,
    }
}

option_chrome.add_experimental_option("prefs", prefs)

# chrome driver
web_driver = webdriver.Chrome(
    service=f"{path_location}/pconfig/chromedriver", options=option_chrome
)  # <- options로 변경


class NewsParsingDrive(metaclass=ABCMeta):
    """
    유틸리티
    """

    def __init__(self, count: int, data: str, site: str) -> None:
        """
        Args:
            count        (int): 크롤링할 데이터의 카운트
            data         (str): 크롤링할 데이터
            site         (str): 크롤링 호출 사이트
        """
        self.count = count
        self.data = data
        self.logger = log(f"{site}", f"{path_location}/log/info.log")

    @abstractmethod
    def get_build_header(self) -> dict[str, str]:
        """parsing authentication header key

        Returns:
            dict[str, Any]: header key
        """
        return NotImplementedError()

    @abstractmethod
    def get_build_url(self) -> str:
        """api site url

        Args:
            url (str): url

        Returns:
            str: url
        """
        return NotImplementedError()

    async def url_parsing(
        self, url: str, headers: dict[str, Any]
    ) -> Coroutine[Any, Any, Any]:
        """
        url parsing
        """
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=headers) as resp:
                match resp.status:
                    case 200:
                        return await resp.json()
                    case _:
                        raise requests.exceptions.RequestException(
                            f"API Request에 실패하였습니다 status code --> {resp.status}"
                        )

    async def get_news_data(
        self, target: str, items: str, titles: str, link: str
    ) -> Coroutine[Any, Any, None]:
        """new parsing

        Args:
            target (str): 타겟 API
            items (str): 첫번째 접근
            title (str): 타이틀
            link (str): url

        Returns:
            _type_: str
        """
        res_data = await self.url_parsing(self.get_build_url(), self.get_build_header())

        count = 0
        for item in res_data[items]:
            title = item[titles]
            url = item[link]
            count += 1

            print(f"{target} Title: {title}")
            print(f"{target} URL: {url}")
            print("--------------------")
        self.logger.info("%s parsing data --> %s", target, count)


class NaverNewsParsingDriver(NewsParsingDrive):
    """네이버 API 호출

    Args:
        SeleniumUtility (_type_): 유틸리티 클래스
    """

    def __init__(self, count: int, data: str) -> None:
        super().__init__(count, data, site="Naver")

    # Args:
    #     count (int, optional): 뉴스 크롤링할 사이트 1 ~ 몇개 까지 가져올까 .
    #     data  (str, optional): 뉴스 크롤링할 사이트 데이터 검색.
    # Function:
    #     naver_news_data
    #         - 파라미터 존재하지 않음
    #         - return 값 None
    #             - items(dict, if NotFound is optional) :
    #                 - items 안에 list가 있음 각 self.data 의 내용의 뉴스가 담겨 있음
    #                     - link -> href
    #                     - title(str, optional) title 존재 안할 수 있음

    def get_build_header(self) -> dict[str, str]:
        return {
            "X-Naver-Client-Id": naver_id,
            "X-Naver-Client-Secret": naver_secret,
        }

    def get_build_url(self) -> str:
        return f"{naver_url}/news.json?query={self.data}&start=1&display={self.count}"

    async def get_naver_news_data(self):
        """
        naver news parsing
        """
        await self.get_news_data(
            target="Naver", items="items", titles="title", link="link"
        )


class DaumNewsParsingDriver(NewsParsingDrive):
    """다음 API 호출

    Args:
        SeleniumUtility (_type_): 유틸리티 클래스
    """

    def __init__(self, count: int, data: str) -> None:
        super().__init__(count, data, site="Daum")

    # Args:
    #     count (int, optional): 뉴스 크롤링할 사이트 1 ~ 몇개 까지 가져올까 .
    #     data (str, optional): 뉴스 크롤링할 사이트 데이터 검색.
    # Function:
    #     get_daum_news_data
    #         - 파라미터 존재하지 않음
    #         - return 값 None
    #             - documents(dict, if NotFound is optional) :
    #                 - documents 안에 list가 있음 각 self.data 의 내용의 뉴스
    #                     - url -> href
    #                     - title(str, optional) title 존재 안할 수 있음

    def get_build_header(self) -> dict[str, str]:
        return {"Authorization": daum_auth}

    def get_build_url(self) -> str:
        return (
            f"{daum_url}/web?sort=accuracy&page=1&size={self.count}&query={self.data}"
        )

    async def get_daum_news_data(self) -> None:
        """
        daum news parsing
        """
        await self.get_news_data(
            target="Daum", items="documents", titles="title", link="url"
        )


class KorbitSymbolParsingUtility(CoinSymbolParsingDriver):
    """Korbit 심볼

    Args:
        SeleniumUtility (_type_): 유틸리티 클래스
    """

    def __init__(self) -> None:
        self.url = "https://www.korbit.co.kr/market"
        self.driver: webdriver.Chrome = web_driver

    def korbit_page(self) -> None:
        """
        url parsing
        """
        self.driver.get(self.url)
        time.sleep(2)
        symbol = self.korbit_parsing_page(html_data=self.driver.page_source)
        csv_saving(data=symbol, csv_file_name="korbit.csv")


class BithumSymbolParsingUtility(CoinSymbolParsingDriver):
    """빗썸 심볼

    Args:
        SeleniumUtility (_type_): 유틸리티 클래스
    """

    def __init__(self) -> None:
        self.url = "https://www.bithumb.com/react/"
        self.driver: webdriver.Chrome = web_driver

    def close_bit_page_and_get_source(self) -> None:
        """
        url parsing
        """
        self.driver.get(url=self.url)
        pop_up_button = WebDriverWait(self.driver, WAIT_TIME).until(
            EC.presence_of_element_located((By.XPATH, BITHUM_POPUP_BUTTON))
        )
        pop_up_button.click()
        symbol = self.bithum_parsing_page(html_data=self.driver.page_source)
        csv_saving(data=symbol, csv_file_name="bithum.csv")
