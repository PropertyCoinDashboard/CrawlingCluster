import time
import urllib3
from typing import Any
from urllib3 import exceptions

from selenium import webdriver
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException


from parsing.coin_parsing_drive import korbit_parsing_page, bithum_parsing_page
from parsing.google_bing_parsing_drive import (
    GoogleNewsCrawlingParsingDrive,
    BingNewsCrawlingParsingDrive,
)
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
# from webdriver_manager.chrome import ChromeDriverManager
# from selenium.webdriver.chrome.service import Service as ChromeService
# web_driver = webdriver.Chrome(
#     service=ChromeService("chromedriver"),
#     options=option_chrome,
# )

# Disable warnings for insecure requests
urllib3.disable_warnings(exceptions.InsecureRequestWarning)

remote_webdriver = "remote_chromedriver"
with webdriver.Remote(
    f"{remote_webdriver}:4444/wd/hub", options=option_chrome
) as driver:
    # Scraping part
    class PageUtilityDriver:
        """
        Homepage Parsing
        """

        def __init__(self, url: str | None) -> None:
            self.url = url
            self.driver: webdriver.Chrome = driver

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

    class GoogleMovingElementsLocation(
        PageUtilityDriver, GoogleNewsCrawlingParsingDrive
    ):
        """Google 셀레니움 요소 움직이기

        Args:
            PageUtilityDriver (str): HTML page 요소들
        """

        def __init__(self, target: str, count: int) -> None:
            self.url = f"https://www.google.com/search?q={target}"
            self.count = count

            super().__init__(url=self.url)

        def search_box_page_type(self, xpath: str) -> Any:
            try:
                news_box_type: Any = WebDriverWait(self.driver, WAIT_TIME).until(
                    EC.presence_of_element_located((By.XPATH, xpath))
                )
                return news_box_type
            except TimeoutException:
                return None

        def handle_news_box_scenario(self, xpath: str) -> None:
            news_box = self.search_box_page_type(xpath)
            if news_box:
                news_box.click()
                self.page_scroll_moving()
                self.next_page_moving()

        def search_box(self) -> str:
            """
            google 자동화할시 3가지 컨셉의 html이 있는걸 확인하여
            각 시나리오마다 Xpath를 각기 적용하여 회피하였음
            """
            self.driver.get(self.url)

            for xpath in [
                GOOGLE_NEWS_TAB_XPATH1,
                GOOGLE_NEWS_TAB_XPATH2,
                GOOGLE_NEWS_TAB_XPATH3,
            ]:
                self.handle_news_box_scenario(xpath)

        def page_scroll_moving(self) -> None:
            """
            google 스크롤 계산 내리기 5번에 걸쳐서 내리기
            """
            prev_height: int = self.driver.execute_script(
                "return document.body.scrollHeight"
            )
            for i in range(1, SCROLL_ITERATIONS):
                time.sleep(5)
                scroll_cal: int = prev_height / SCROLL_ITERATIONS * i
                self.driver.execute_script(f"window.scrollTo(0, {scroll_cal})")

        def next_page_moving(self) -> None:
            """
            다음페이지로 넘어가기
            """
            for i in range(3, self.count + 1):
                next_page_button = self.search_box_page_type(
                    f'//*[@id="botstuff"]/div/div[3]/table/tbody/tr/td[{i}]/a'
                )
                if next_page_button:
                    self.news_info_collect(self.driver.page_source)
                    next_page_button.click()
                    time.sleep(5)
                    self.page_scroll_moving()

    class BingMovingElementLocation(PageUtilityDriver, BingNewsCrawlingParsingDrive):
        """빙 홈페이지 크롤링

        Args:
            PageUtilityDriver (str): html
            BingNewsCrawlingParsingDrive (class): parsingDrive
        """

        def __init__(self, target: str, count: int) -> None:
            self.url = f"https://www.bing.com/news/search?q={target}"
            self.count = count
            super().__init__(url=self.url)

        def repeat_scroll(self):
            self.driver.get(self.url)

            # 스크롤 내리기 전 위치
            scroll_location: int = self.driver.execute_script(
                "return document.body.scrollHeight"
            )

            i = 0
            while i < self.count:
                # 현재 스크롤의 가장 아래로 내림
                self.driver.execute_script(
                    "window.scrollTo(0,document.body.scrollHeight)"
                )

                # 전체 스크롤이 늘어날 때까지 대기
                time.sleep(5)

                # 늘어난 스크롤 높이
                scroll_height: int = self.driver.execute_script(
                    "return document.body.scrollHeight"
                )
                i += 1

                # page url
                self.news_info_collect(self.driver.page_source)
                # 늘어난 스크롤 위치와 이동 전 위치 같으면(더 이상 스크롤이 늘어나지 않으면) 종료
                if scroll_location == scroll_height:
                    break

                # 같지 않으면 스크롤 위치 값을 수정하여 같아질 때까지 반복
                else:
                    # 스크롤 위치값을 수정
                    scroll_location = self.driver.execute_script(
                        "return document.body.scrollHeight"
                    )

    class KorbitSymbolParsingUtility(PageUtilityDriver):
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
            symbol = korbit_parsing_page(html_data=self.driver.page_source)
            csv_saving(data=symbol, csv_file_name="korbit.csv")

    class BithumSymbolParsingUtility(PageUtilityDriver):
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
                symbol = bithum_parsing_page(html_data=self.driver.page_source)
                csv_saving(data=symbol, csv_file_name="bithum.csv")
