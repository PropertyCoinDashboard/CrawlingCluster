"""
Xpath 모음집..
"""

from typing import Literal

# 웹사이트 element xpath location
GOOGLE_SEARCH_XPATH: Literal = '//*[@name="q"]'
BING_SEARCH_XPATH: Literal = '//*[@id="sb_form_q"]'

# news element xpath location
GOOGLE_NEWS_TAB_XPATH2: Literal = '//*[@id="cnt"]/div[5]/div/div/div/div[1]/div/a[1]'
GOOGLE_NEWS_TAB_XPATH: Literal = '//*[@id="hdtb-msb"]/div[1]/div/div[2]/a'
BING_NEWS_TAB_XPATH: Literal = '//*[@id="b-scopeListItem-news"]/a'

USERAGENT: Literal = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) \
    AppleWebKit/537.36 (KHTML, like Gecko) Chrome/110.0.0.0 Safari/537.36"


# bithum_popup
BITHUM_POPUP_BUTTON: Literal = (
    '//*[@id="popUpContainer"]/div/div/div/div/div/div[2]/button'
)


# waiting time
PAGE_LOAD_DELAY: Literal = 2
WAIT_TIME: Literal = 2
