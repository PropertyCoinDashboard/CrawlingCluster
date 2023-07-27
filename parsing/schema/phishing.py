import re
import math

import requests
import urllib3
from typing import *
from urllib.parse import urlparse
from urllib.error import URLError
from urllib3.exceptions import InsecureRequestWarning

from tld import get_tld
from googlesearch import search

import pandas as pd
from bs4 import BeautifulSoup


urllib3.disable_warnings(InsecureRequestWarning)


class PhishingPreprocessing:
    def __init__(self, url: str) -> None:
        self.url = url

    def entropy(self) -> float | int:
        string = self.url.strip()
        prob: list[float] = [
            float(string.count(c)) / len(string) for c in dict.fromkeys(list(string))
        ]
        entropy = -sum([(p * math.log(p) / math.log(2.0)) for p in prob])
        return entropy

    def path_entropy(self) -> float | int:
        string = urlparse(self.url).path.strip()
        path_prob = [
            float(string.count(c)) / len(string) for c in dict.fromkeys(list(string))
        ]
        path_entropy = -sum([(p * math.log(p) / math.log(2.0)) for p in path_prob])
        return path_entropy

    def hostname_length(self) -> int:
        return len(urlparse(self.url).netloc)

    def path_length(self) -> int:
        return len(urlparse(self.url).path)

    def tld_length(self) -> int:
        try:
            return len(get_tld(self.url, fail_silently=True))
        except:
            return -1

    def special_character(self) -> int:
        count = (
            self.url.count("?")
            + self.url.count("#")
            + self.url.count(".")
            + self.url.count("=")
        )
        return count

    def count_http(self) -> int:
        return self.url.count("http")

    def count_https(self) -> int:
        return self.url.count("https")

    def count_www(self) -> int:
        return self.url.count("www")

    def numDigits(self) -> int:
        digits = [i for i in self.url if i.isdigit()]
        return len(digits)

    def letter_count(self) -> int:
        letters = 0
        for i in self.url:
            if i.isalpha():
                letters = letters + 1
        return letters

    def no_of_dir(self) -> int:
        urldir = urlparse(self.url).path
        return urldir.count("/")

    def url_length(self) -> Literal[1, -1, 0]:
        if len(self.url) < 54:
            return 1
        elif 54 <= len(self.url) <= 75:
            return 0
        else:
            return -1

    def google_index(self) -> Literal[1, -1]:
        try:
            site = search(self.url, 5)
            return 1 if site else -1
        except (
            requests.exceptions.ConnectionError,
            requests.exceptions.HTTPError,
            requests.exceptions.TooManyRedirects,
            URLError,
            requests.exceptions.InvalidSchema,
        ):
            return -1

    def having_symbol(self) -> Literal[1, -1]:
        search_symbol = re.search("@", self.url)
        return -1 if search_symbol else 1

    def prefix_suffix(self) -> Literal[1, -1]:
        search_suffix = re.search("-", self.url)
        return -1 if search_suffix else 1

    def redirection(self) -> Literal[1, -1]:
        url_parser = urlparse(self.url)
        path = url_parser.path
        if "//" in path:
            return -1
        else:
            return 1

    def sfh(self) -> Literal[1, -1, 0]:
        try:
            resp = requests.get(
                self.url,
                headers={"User-Agent": "Mozilla/5.0"},
                verify=False,
                timeout=10,
            ).content
            soup = BeautifulSoup(resp, "html.parser")
            for form in soup.find_all("form", action=True):
                if form["action"] == "" or form["action"] == "about:blank":
                    return -1
                elif self.url not in form["action"] and self.url not in form["action"]:
                    return 0
                else:
                    return 1
            return 1
        except (
            requests.exceptions.ConnectionError,
            requests.exceptions.ReadTimeout,
            requests.exceptions.TooManyRedirects,
            URLError,
            requests.exceptions.InvalidSchema,
        ):
            return -1

    def shortening_service(self) -> Literal[1, -1]:
        match = re.search(
            "bit\.ly|goo\.gl|shorte\.st|go2l\.ink|x\.co|ow\.ly|t\.co|tinyurl|tr\.im|is\.gd|cli\.gs|"
            "yfrog\.com|migre\.me|ff\.im|tiny\.cc|url4\.eu|twit\.ac|su\.pr|twurl\.nl|snipurl\.com|"
            "short\.to|BudURL\.com|ping\.fm|post\.ly|Just\.as|bkite\.com|snipr\.com|fic\.kr|loopt\.us|"
            "doiop\.com|short\.ie|kl\.am|wp\.me|rubyurl\.com|om\.ly|to\.ly|bit\.do|t\.co|lnkd\.in|"
            "db\.tt|qr\.ae|adf\.ly|goo\.gl|bitly\.com|cur\.lv|tinyurl\.com|ow\.ly|bit\.ly|ity\.im|"
            "q\.gs|is\.gd|po\.st|bc\.vc|twitthis\.com|u\.to|j\.mp|buzurl\.com|cutt\.us|u\.bb|yourls\.org|"
            "x\.co|prettylinkpro\.com|scrnch\.me|filoops\.info|vzturl\.com|qr\.net|1url\.com|tweez\.me|v\.gd|"
            "tr\.im|link\.zip\.net",
            self.url,
        )
        if match:
            return -1
        else:
            return 1

    def making_data(self) -> pd.DataFrame:
        data_ = {
            "url": [self.url],
            "entropy": [self.entropy()],
            "path_entropy": [self.path_entropy()],
            "hostname_length": [self.hostname_length()],
            "path_length": [self.path_length()],
            "tld_length": [self.tld_length()],
            "count-": [self.prefix_suffix()],
            "count-@": [self.having_symbol()],
            "special_chapter": [self.special_character()],
            "count-http": [self.count_http()],
            "count-https": [self.count_https()],
            "count-www": [self.count_www()],
            "count-digit": [self.numDigits()],
            "count-letter": [self.letter_count()],
            "count_dir": [self.no_of_dir()],
            "redirection": [self.redirection()],
            "google_index": [self.google_index()],
            "url_length": [self.url_length()],
            "sfh": [self.sfh()],
            "short_url_service": [self.shortening_service()],
        }
        data = pd.DataFrame(data_)
        print(data)

        return data
