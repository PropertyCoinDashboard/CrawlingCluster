import time
import random
import urllib3


from typing import Any, Callable
from urllib3 import exceptions
from collections import deque

import undetected_chromedriver as uc
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from selenium.common.exceptions import (
    InvalidSessionIdException,
    NoSuchElementException,
    WebDriverException,
)
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities

from fake_useragent import UserAgent

from parsing.drive.gb_parsing_drive import (
    GoogleNewsCrawlingParsingDrive,
    BingNewsCrawlingParsingDrive,
)
from parsing.util._typing import UrlCollect
from parsing.config._xpath_location import (
    WAIT_TIME,
    SCROLL_ITERATIONS,
)

# Disable warnings for insecure requests
urllib3.disable_warnings(exceptions.InsecureRequestWarning)

ua = UserAgent()


def chrome_option_injection() -> webdriver.Chrome:
    # 크롬 옵션 설정
    option_chrome = uc.ChromeOptions()
    option_chrome.add_argument("headless")
    option_chrome.add_argument("--disable-gpu")
    option_chrome.add_argument("--disable-infobars")
    option_chrome.add_argument("--disable-extensions")
    option_chrome.add_argument("--no-sandbox")
    option_chrome.add_argument("--disable-dev-shm-usage")
    option_chrome.add_argument(f"user-agent={ua.random}")

    caps = DesiredCapabilities().CHROME
    # page loading 없애기
    caps["pageLoadStrategy"] = "none"

    prefs = {
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
    # webdriver_remote = webdriver.Remote(
    #     "http://0.0.0.0:4444/wd/hub", options=option_chrome
    # )
    from webdriver_manager.chrome import ChromeDriverManager
    from selenium.webdriver.chrome.service import Service as ChromeService

    webdriver_remote = webdriver.Chrome(
        service=ChromeService(ChromeDriverManager().install()), options=option_chrome
    )
    return webdriver_remote


class GoogleMovingElementsLocation(GoogleNewsCrawlingParsingDrive):
    """구글 홈페이지 크롤링

    Args:
        GoogleNewsCrawlingParsingDrive (class): parsingDrive
    """

    def __init__(self, target: str, count: int) -> None:
        """
        Args:
            target (str): 검색 타겟
            count (int): 얼마나 수집할껀지
        """
        self.url = f"https://www.google.com/search?q={target}&tbm=nws&gl=ko&hl=kr"
        self.driver: webdriver.Chrome = chrome_option_injection()
        self.count = count

    def page_scroll_moving(self) -> None:
        """
        google 스크롤 계산 내리기 5번에 걸쳐서 내리기
        """
        prev_height: int = self.driver.execute_script(
            "return document.body.scrollHeight"
        )
        for i in range(1, SCROLL_ITERATIONS):
            time.sleep(5)
            scroll_cal: float = prev_height / SCROLL_ITERATIONS * i
            self.driver.execute_script(f"window.scrollTo(0, {scroll_cal})")

    def search_box_page_type(self, xpath: str) -> Any:
        """xpath 요소 찾기"""
        news_box_type: Any = WebDriverWait(self.driver, WAIT_TIME).until(
            EC.presence_of_element_located((By.XPATH, xpath))
        )
        return news_box_type

    def a_loop_page(self, start: int, xpath_type: Callable[[int], str]) -> UrlCollect:
        """페이지 수집하면서 이동

        Args:
            start (int): 페이지 이동 시작 html location
            xpath_type (Callable[[int], str]): google은 여러 HTML 이므로 회피 목적으로 xpath 함수를 만듬
        """
        data = deque()
        try:
            for i in range(start, self.count + start):
                next_page_button: Any = self.search_box_page_type(xpath_type(i))
                print(f"{i-1}page로 이동합니다 --> {xpath_type(i)} 이용합니다")
                url_data: list[str] = self.news_info_collect(self.driver.page_source)
                data.append(url_data)
                next_page_button.click()
                time.sleep(5)
                self.page_scroll_moving()
            else:
                print("google 수집 종료")
                self.driver.quit()
        except (NoSuchElementException, WebDriverException) as e:
            print(f"해당 이유로 인해 수집을 다시 시도합니다 --> {e}")
            self.driver.refresh()
        return data

    def next_page_moving(self) -> UrlCollect:
        """페이지 수집 이동 본체"""

        def mo_xpath_injection(start: int) -> str:
            """google mobile xpath 경로 start는 a tag 기점 a -> a[2]"""
            if start == 2:
                return f'//*[@id="wepR4d"]/div/span/a'
            return f'//*[@id="wepR4d"]/div/span/a[{start-1}]'

        def pa_xpath_injection(start: int) -> str:
            """google site xpath 경로 start는 tr/td[3](page 2) ~ 기점"""
            return f'//*[@id="botstuff"]/div/div[3]/table/tbody/tr/td[{start}]/a'

        # 실행시작 지점
        self.driver.get(self.url)
        try:
            return self.a_loop_page(3, pa_xpath_injection)
        except NoSuchElementException:
            return self.a_loop_page(2, mo_xpath_injection)
        except WebDriverException as e:
            print(f"다음과 같은 이유로 google 수집 종료 --> {e}")
            print("webserver 다시 시작합니다")
            self.driver.refresh()

    def search_box(self) -> UrlCollect:
        """수집 시작점
        - self.page_scroll_moving()
            - page 내리기
        - self.next_page_moving()
            - 다음 page 이동
        """
        self.driver.get(self.url)
        self.page_scroll_moving()
        return self.next_page_moving()


class BingMovingElementLocation(BingNewsCrawlingParsingDrive):
    """빙 홈페이지 크롤링

    Args:
        BingNewsCrawlingParsingDrive (class): parsingDrive
    """

    def __init__(self, target: str, count: int) -> None:
        """
        Args:
            target (str): 검색 타겟
            count (int): 얼마나 수집할껀지
        """
        self.url = f"https://www.bing.com/news/search?q={target}"
        self.count = count
        self.driver: webdriver.Remote = chrome_option_injection()

    def repeat_scroll(self) -> UrlCollect:
        """Bing은 무한 스크롤이기에 횟수만큼 페이지를 내리도록 하였음"""
        self.driver.get(self.url)
        # 스크롤 내리기 전 위치
        scroll_location: int = self.driver.execute_script(
            "return document.body.scrollHeight"
        )
        try:
            i = 0
            data: UrlCollect = deque()
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
                url_element: list[str] = self.news_info_collect(self.driver.page_source)
                data.append(url_element)

                # 늘어난 스크롤 위치와 이동 전 위치 같으면(더 이상 스크롤이 늘어나지 않으면) 종료
                if scroll_location == scroll_height:
                    break

                # 같지 않으면 스크롤 위치 값을 수정하여 같아질 때까지 반복
                else:
                    # 스크롤 위치값을 수정
                    scroll_location = self.driver.execute_script(
                        "return document.body.scrollHeight"
                    )
            time.sleep(5)
            return data
        except InvalidSessionIdException:
            pass
        finally:
            print("Bing 수집 종료")
            self.driver.quit()
