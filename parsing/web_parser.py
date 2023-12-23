"""
This module contains classes for parsing web pages.
"""
import re
import time
import configparser
from typing import Any
from pathlib import Path
from dataclasses import dataclass, asdict

import urllib3
from urllib3 import exceptions
from bs4 import BeautifulSoup, ResultSet

from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By

from parsing.schema.util_parser import csv_saving
from parsing.schema.xpath_location import USERAGENT, WAIT_TIME, BITHUM_POPUP_BUTTON
from parsing.web_parser import CoinSymbolParsingDriver
from webdriver_manager.chrome import ChromeDriverManager


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
    service=ChromeService(ChromeDriverManager().install()), options=option_chrome
)

# Disable warnings for insecure requests
urllib3.disable_warnings(exceptions.InsecureRequestWarning)


def soup_data(
    html_data: str, element: str, elements: dict[str, str]
) -> ResultSet[Any] | list:
    """
    Parse the HTML data using BeautifulSoup
    """
    soup = BeautifulSoup(html_data, "lxml")
    search_results: ResultSet[Any] = soup.find_all(element, elements)
    return search_results if search_results else []


@dataclass
class CoinSymbolSchema:
    """
    Data class for Coin symbol
    """

    coin_symbol: str
    korean_name: str


class CoinSymbolParsingDriver:
    """
    Class for parsing Coin symbol
    """

    def korbit_parsing_page(self, html_data: str) -> list[CoinSymbolSchema]:
        """
        Parse Korbit page
        """
        crypto_list: list[CoinSymbolSchema] = []
        market_data = soup_data(
            html_data=html_data, element="div", elements={"id": "cryptosM"}
        )
        for market_div in market_data:
            for item_div in market_div.find_all(
                "div", {"class": "market-list-items hover:bg-slate-50"}
            ):
                for item in item_div.find_all(
                    "div", {"class": "inline-flex items-center"}
                ):
                    time.sleep(2)
                    coin_symbol_span: str = item_div.find(
                        "span", {"class": "text-slate-400 text-sm"}
                    )
                    data = CoinSymbolSchema(
                        coin_symbol=coin_symbol_span.text,
                        korean_name=item.text,
                    )
                    crypto_list.append(asdict(data))

        return crypto_list

    def bithum_parsing_page(self, html_data: str) -> list[CoinSymbolSchema]:
        """
        Parse Bithum page
        """
        crypto_list: list[CoinSymbolSchema] = []
        market_data: list = soup_data(
            html_data=html_data,
            element="div",
            elements={"class": "MarketTable_market-wrap-list__2fKBD"},
        )
        for market_div in market_data:
            for row in market_div.find_all(
                "tr", {"class": "MarketRow_market-row__ZzE1-"}
            ):
                time.sleep(2)
                for anchor in row.find_all("a"):
                    for strong in anchor.find_all("strong"):
                        hangle: str = re.sub("[a-zA-z]", "", strong.text)
                        anchor_span = anchor.find(
                            "span", {"class": "MarketRow_sort-coin__aIyw1"}
                        )
                        data = CoinSymbolSchema(
                            coin_symbol=anchor_span.text.split("/")[0],
                            korean_name=hangle.replace(" ", ""),
                        )

                        crypto_list.append(asdict(data))

        return crypto_list


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


class GoogleUtilityDriver:
    def __init__(self, driver=web_driver) -> None:
        self.url = f"https://www.google.com"
        self.driver = driver

    def page(self) -> str:
        self.driver.get(self.url)
        return self.driver.page_source
