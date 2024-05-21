import os
import urllib.parse
import json
import aiohttp
import asyncio
from typing import List, Dict, Tuple
import random
from bs4 import BeautifulSoup


class NewsSearch:
     def __init__(self, n_client_id, n_client_secret, d_kakao_api_key):
          self.n_client_id = n_client_id
          self.n_client_secret = n_client_secret
          self.d_kakao_api_key = d_kakao_api_key

     async def get_naver_news_urls(self, query, max_results=1000, results_per_request=100):
          """
          Naver 뉴스 검색 API를 사용하여 뉴스 URL 목록을 가져옵니다.

          Args:
               query (str): 검색어
               max_results (int, optional): 최대 검색 결과 수. 기본값은 1000.
               results_per_request (int, optional): 한 번의 요청으로 가져올 결과 수. 기본값은 100.

          Returns:
               List[str]: 뉴스 URL 목록
          """
          base_url = "https://openapi.naver.com/v1/search/news.json"
          query = urllib.parse.quote(query)
          
          urls = []
          async with aiohttp.ClientSession() as session:
               for start in range(1, max_results + 1, results_per_request):
                    url = f"{base_url}?query={query}&display={results_per_request}&start={start}&sort=date"
                    headers = {
                         "X-Naver-Client-Id": self.n_client_id,
                         "X-Naver-Client-Secret": self.n_client_secret
                    } # 빼서 적용
                    try:
                         async with session.get(url, headers=headers) as response:
                              if response.status == 200:
                                   response_body = await response.text()
                                   news_items = json.loads(response_body).get("items", [])
                                   for item in news_items:
                                        urls.append(item.get("link"))
                              else:
                                   print(f"Error Code: {response.status}")
                    except aiohttp.ClientError as e:
                         print(f"Request Error: {e}")
          
          return urls

     async def get_daum_news_urls(self, search_query: str, total_pages: int = 11) -> List[str]:
          """
          Daum 검색 엔진을 사용하여 뉴스 URL 목록을 가져옵니다.

          Args:
               search_query (str): 검색어
               total_pages (int, optional): 검색할 총 페이지 수. 기본값은 11.

          Returns:
               List[str]: 뉴스 URL 목록
          """
          url = "https://search.daum.net/search"
          params = {
               'nil_suggest': 'btn',
               'w': 'news',
               'DA': 'STC',
               'cluster': 'y',
               'q': search_query,
               'sort': 'accuracy'
          }

          async with aiohttp.ClientSession() as session:
               all_urls = []
               for page in range(1, total_pages + 1):
                    params['p'] = page
                    html = await self.fetch(session, url, params)
                    news_urls = self.extract_news_urls(html)
                    all_urls.extend(news_urls)
                    await asyncio.sleep(random.uniform(2, 5))  # 페이지 변경 시 랜덤 지연 추가 (사람처럼 보이기 위해)
               return all_urls
     async def fetch(self, session: aiohttp.ClientSession, url: str, params: Dict[str, str],headers) -> str:
          """
          주어진 URL에 GET 요청을 보내고 HTML 응답을 반환합니다.

          Args:
               session (aiohttp.ClientSession): Aiohttp 클라이언트 세션
               url (str): 요청할 URL
               params (Dict[str, str]): URL에 추가할 매개변수
               headers (Dict[str,str]): Header값 
          Returns:
               str: HTML 응답
          """
          async with session.get(url, params=params, headers=headers) as response:
               response.raise_for_status()
               return await response.text() 
              
     @staticmethod
     def extract_news_urls(html: str) -> List[str]:
          """
          HTML에서 뉴스 URL을 추출합니다.

          Args:
               html (str): HTML 문자열

          Returns:
               List[str]: 뉴스 URL 목록
          """
          soup = BeautifulSoup(html, 'html.parser')
          news_urls = []
          ul_tag = soup.find('ul', class_='list_news')
          if ul_tag:
               li_tags = ul_tag.find_all('li')
               for li in li_tags:
                    a_tag_title = li.find('a', class_='tit_main fn_tit_u')
                    if a_tag_title:
                         news_urls.append(a_tag_title['href'])
          return news_urls
     
     @staticmethod
     def data_structure() -> Dict[int, Dict[int, List[str]]]:
          """
          데이터를 저장할 구조를 생성합니다.

          Returns:
               Dict[int, Dict[int, List[str]]]: 데이터 구조
          """
          return {
               i: (
                    {j: [] for j in range(1, 5)}
                    if i == 1
                    else (
                         {j: [] for j in range(5, 7)}
                         if i == 2
                         else (
                              {j: [] for j in range(7, 9)}
                              if i == 3
                              else {j: [] for j in range(9, 11)}
                         )
                    )
               )
               for i in range(1, 5)
          }
     
     @staticmethod
     def distribute_urls(data: Dict[int, Dict[int, List[str]]], urls: List[str], start: Tuple[int, int]) -> Tuple[Dict[int, Dict[int, List[str]]], Tuple[int, int]]:
          """
          URL 목록을 데이터 구조에 분배합니다.

          Args:
               data (Dict[int, Dict[int, List[str]]]): 데이터 구조
               urls (List[str]): URL 목록
               start (Tuple[int, int]): 분배를 시작할 위치

          Returns:
               Tuple[Dict[int, Dict[int, List[str]]], Tuple[int, int]]: 업데이트된 데이터 구조와 마지막 위치
          """
          url_index = 0
          num_urls = len(urls)
          i, j = start

          while url_index < num_urls and i <= 4:
               if j in data[i]:
                    data[i][j].extend(urls[url_index:num_urls])
                    url_index = num_urls
                    j += 1
                    if j not in data[i]:
                         i += 1
                         if i <= 4:
                              j = min(data[i].keys())
               else:
                    i += 1
                    if i <= 4:
                         j = min(data[i].keys())
          return data, (i, j)

     @staticmethod
     def save_to_json(data, filename="news_urls.json"):
          """
          데이터를 JSON 파일로 저장합니다.

          Args:
               data (dict): 저장할 데이터
               filename (str, optional): 저장할 파일명. 기본값은 "news_urls.json".
          """
          try:
               with open(filename, 'w', encoding='utf-8') as json_file:
                    json.dump(data, json_file, ensure_ascii=False, indent=4)
               print(f"Data successfully saved to {filename}")
          except IOError as e:
               print(f"File Error: {e}")
