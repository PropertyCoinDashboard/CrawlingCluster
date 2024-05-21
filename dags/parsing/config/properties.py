import os
import configparser
from pathlib import Path

# 부모 경로
path_location = Path(os.getcwd())
# key_parser
parser = configparser.ConfigParser()
parser.read(f"{path_location}/parsing/config/url.conf")

naver_id: str = parser.get("naver", "X-Naver-Client-Id")
naver_secret: str = parser.get("naver", "X-Naver-Client-Secret")
naver_url: str = parser.get("naver", "NAVER_URL")

daum_auth: str = parser.get("daum", "Authorization")
daum_url: str = parser.get("daum", "DAUM_URL")

D_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
    "Accept-Language": "ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7,zh-CN;q=0.6,zh;q=0.5",
    "Cache-Control": "max-age=0",
    "Cookie": "uvkey=a618a2f7-9cfa-47a7-87be-2a8438bb2a0a; __T_=1; SCH_SORT=; _ksk=71318326-8d64-4d9e-8e28-e9799b90323c; DTQUERY=%EB%B9%84%ED%8A%B8%EC%BD%94%EC%9D%B8; ODT=DNSZ_DICZ_GG2Z_TWAZ_LB2Z_IIMZ_SNYZ; DDT=IVRZ_MS2Z_VOIZ_1DVZ; SHOW_DNS=0; _T_ANO=XgDlyXlluPw4bfHj2uEw7tIXfaugtx8VkVCnX23UEwTpJzjUUGD6JJ2wRc/NdN8UHqESOF3NlsQT1XV7oKDS6AR5wifjbmfoS6+/oIvC2uMAYEC5AAJ7UPQEkDtyNUHAIZMYLino9LLJah6DqacmSkmVTa1o6HAC0nZ10vhQAfrxn34mOD4Gq7VMGh9SoTAcdiVQTKwfJq+TYMkDDFrRgAgsrJXFCUxdCx/+Y9cDOvWUR890s0FCi6O8NC8iCleSpIkegcyIdVgFMhPAGK6BmMKy5iAAhokDONA5iBTybtT10ByVyRtRINWzQwxjLSwfl6zFf9voRMnvQU1QFVNsHg==",
    "Referer": "https://search.daum.net/search?nil_suggest=btn&w=news&DA=STC&cluster=y&q=%EB%B9%84%ED%8A%B8%EC%BD%94%EC%9D%B8&p=1&sort=recency",
    "Sec-Ch-Ua": '"Chromium";v="124", "Google Chrome";v="124", "Not-A.Brand";v="99"',
    "Sec-Ch-Ua-Arch": '"x86"',
    "Sec-Ch-Ua-Bitness": '"64"',
    "Sec-Ch-Ua-Full-Version-List": '"Chromium";v="124.0.6367.119", "Google Chrome";v="124.0.6367.119", "Not-A.Brand";v="99.0.0.0"',
    "Sec-Ch-Ua-Mobile": "?0",
    "Sec-Ch-Ua-Model": '""',
    "Sec-Ch-Ua-Platform": '"Windows"',
    "Sec-Ch-Ua-Platform-Version": '"10.0.0"',
    "Sec-Ch-Ua-Wow64": "?0",
    "Sec-Fetch-Dest": "document",
    "Sec-Fetch-Mode": "navigate",
    "Sec-Fetch-Site": "same-origin",
    "Sec-Fetch-User": "?1",
    "Upgrade-Insecure-Requests": "1",
}
