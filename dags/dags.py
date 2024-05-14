"""
기능 테스트
"""

from parsing.selenium_parsing import (
    GoogleMovingElementsLocation,
    BingMovingElementLocation,
)


def process_google() -> None:
    GoogleMovingElementsLocation("비트코인", 5).search_box()


def process_bing() -> None:
    BingMovingElementLocation("비트코인", 5).repeat_scroll()


process_google()
