"""
This module contains classes for parsing web pages.
"""
import time
import urllib3
from urllib3 import exceptions

from selenium.common.exceptions import TimeoutException
from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager


from parsing.util.util_parser import csv_saving
from parsing.util.xpath_location import USERAGENT, WAIT_TIME, BITHUM_POPUP_BUTTON
from parsing.kb_coin_symbol_parsing.coin_parsing_driver import CoinSymbolParsingDriver


# 크롬 옵션 설정
option_chrome = webdriver.ChromeOptions()
option_chrome.add_argument("headless")
option_chrome.add_argument("disable-gpu")
option_chrome.add_argument("disable-infobars")
option_chrome.add_argument("--disable-extensions")
option_chrome.add_argument("user-agent=" + USERAGENT)


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
web_driver = webdriver.Chrome(service=ChromeService(ChromeDriverManager().install()))

# Disable warnings for insecure requests
urllib3.disable_warnings(exceptions.InsecureRequestWarning)


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
        try:
            pop_up_button = WebDriverWait(self.driver, WAIT_TIME).until(
                EC.presence_of_element_located((By.XPATH, BITHUM_POPUP_BUTTON))
            )
            pop_up_button.click()
        except TimeoutException:
            symbol = self.bithum_parsing_page(html_data=self.driver.page_source)
            csv_saving(data=symbol, csv_file_name="bithum.csv")


class GoogleUtilityDriver:
    def __init__(self, driver=web_driver) -> None:
        self.url = f"https://www.google.com"
        self.driver = driver

    def page(self) -> str:
        self.driver.get(self.url)
        return self.driver.page_source
