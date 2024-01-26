import time
import urllib3
from typing import Any
from urllib3 import exceptions

from selenium import webdriver
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from webdriver_manager.chrome import ChromeDriverManager


from parsing.coin_parsing_drive import CoinSymbolParsingDriver
from parsing.util.util_parser import csv_saving
from parsing.util._xpath_location import (
    USERAGENT,
    WAIT_TIME,
    BITHUM_POPUP_BUTTON,
    SCROLL_ITERATIONS,
    GOOGLE_NEWS_TAB_XPATH1,
    GOOGLE_NEWS_TAB_XPATH2,
    GOOGLE_NEWS_TAB_XPATH3,
)


# # 크롬 옵션 설정
# option_chrome = webdriver.ChromeOptions()
# option_chrome.add_argument("headless")
# option_chrome.add_argument("disable-gpu")
# option_chrome.add_argument("disable-infobars")
# option_chrome.add_argument("--disable-extensions")
# option_chrome.add_argument("user-agent=" + USERAGENT)


# prefs: dict[str, dict[str, int]] = {
#     "profile.default_content_setting_values": {
#         "cookies": 2,
#         "images": 2,
#         "plugins": 2,
#         "popups": 2,
#         "geolocation": 2,
#         "notifications": 2,
#         "auto_select_certificate": 2,
#         "fullscreen": 2,
#         "mouselock": 2,
#         "mixed_script": 2,
#         "media_stream": 2,
#         "media_stream_mic": 2,
#         "media_stream_camera": 2,
#         "protocol_handlers": 2,
#         "ppapi_broker": 2,
#         "automatic_downloads": 2,
#         "midi_sysex": 2,
#         "push_messaging": 2,
#         "ssl_cert_decisions": 2,
#         "metro_switch_to_desktop": 2,
#         "protected_media_identifier": 2,
#         "app_banner": 2,
#         "site_engagement": 2,
#         "durable_storage": 2,
#     }
# }

# option_chrome.add_experimental_option("prefs", prefs)

# chrome driver
web_driver = webdriver.Chrome(
    service=ChromeService(ChromeDriverManager().install()),
)

# Disable warnings for insecure requests
urllib3.disable_warnings(exceptions.InsecureRequestWarning)


class PageUtilityDriver:
    """
    Homepage Parsing
    """

    def __init__(self, url: str | None = None) -> None:
        self.url = url
        self.driver: webdriver.Chrome = web_driver

    def __exit__(self):
        if self.driver:
            self.driver.quit()

    def page(self) -> str:
        """

        Returns:
            str: HTML source
        """
        self.driver.get(self.url)
        return self.driver.page_source


class GoogleMovingElementsLocation(PageUtilityDriver):
    """Google 셀레니움 요소 움직이기

    Args:
        PageUtilityDriver (str): HTML page 요소들
    """

    def __init__(self, target: str) -> None:
        self.url = f"https://www.google.com/search?q={target}"
        super().__init__(url=self.url)

    def handle_news_box_scenario(self, xpath: str) -> None:
        def search_box_page_type(xpath: str) -> Any:
            news_box_type: Any = WebDriverWait(self.driver, WAIT_TIME).until(
                EC.presence_of_element_located((By.XPATH, xpath))
            )
            return news_box_type

        try:
            news_box = search_box_page_type(xpath)
            news_box.click()
            self.page_scroll_moving()
        except TimeoutException:
            pass  # TimeoutException 무시

    def search_box(self) -> str:
        """
        google 의 page변환 정책으로 각각 요소마다 2중 try 적용
        별로 좋아보이진 않지만 만들어놓고 개선 작업 시작

        """
        self.driver.get(self.url)

        # 시나리오 1 처리
        self.handle_news_box_scenario(GOOGLE_NEWS_TAB_XPATH1)

        # 시나리오 2 처리
        self.handle_news_box_scenario(GOOGLE_NEWS_TAB_XPATH2)

        # 시나리오 3 처리
        self.handle_news_box_scenario(GOOGLE_NEWS_TAB_XPATH3)

        return self.driver.page_source

    def page_scroll_moving(self) -> None:
        """
        google 스크롤 계산 내리기 5번에 걸쳐서 내리기
        """
        prev_height: int = self.driver.execute_script(
            "return document.body.scrollHeight"
        )
        print("현재 높이 :", prev_height)
        for i in range(1, SCROLL_ITERATIONS):
            time.sleep(2)
            self.driver.execute_script(
                f"window.scrollTo(0, {prev_height / SCROLL_ITERATIONS * i})"
            )
            present_height: int = self.driver.execute_script(
                "return document.body.scrollHeight"
            )
            if present_height != 0:
                self.driver.execute_script(
                    f"window.scrollTo(0, {prev_height / SCROLL_ITERATIONS * i})"
                )


class KorbitSymbolParsingUtility(CoinSymbolParsingDriver, PageUtilityDriver):
    """Korbit 심볼

    Args:
        SeleniumUtility (_type_): 유틸리티 클래스
    """

    def __init__(self) -> None:
        super().__init__(url="https://www.korbit.co.kr/market")

    def korbit_page(self) -> None:
        """
        url parsing
        """
        self.driver.get(self.url)
        time.sleep(2)
        symbol = self.korbit_parsing_page(html_data=self.driver.page_source)
        csv_saving(data=symbol, csv_file_name="korbit.csv")


class BithumSymbolParsingUtility(CoinSymbolParsingDriver, PageUtilityDriver):
    """빗썸 심볼

    Args:
        SeleniumUtility (_type_): 유틸리티 클래스
    """

    def __init__(self) -> None:
        super().__init__(url="https://www.bithumb.com/react/")

    def close_bit_page_and_get_source(self) -> None:
        """
        url parsing
        """
        self.driver.get(url=self.url)
        try:
            pop_up_button = WebDriverWait(self.driver, WAIT_TIME).until(
                EC.presence_of_element_located((By.XPATH, BITHUM_POPUP_BUTTON))
            )
            pop_up_button.click()
        except TimeoutException:
            symbol = self.bithum_parsing_page(html_data=self.driver.page_source)
            csv_saving(data=symbol, csv_file_name="bithum.csv")
