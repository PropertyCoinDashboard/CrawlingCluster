# import os
# from dotenv import load_dotenv
# from news_search import NewsSearch
# from pprint import pprint

# # .env 파일에서 환경 변수를 로드
# load_dotenv()

# # 네이버 API 자격증명
# N_Client_ID = os.getenv("N_Client_ID")
# N_Client_Secret = os.getenv("N_Client_Secret")
# D_Kakao_api_key = os.getenv("D_Kakao_api_key")

# # 검색어와 최대 결과 수 설정
# query = "비트코인"
# max_results = 1000  # 최대 1000개의 결과 가져오기

# # naver NewsSearch 클래스 인스턴스 생성
# naver_news_search = NewsSearch(N_Client_ID, N_Client_Secret)
# # 네이버 뉴스 URL 가져오기
# naver_news_urls = naver_news_search.get_naver_news_urls(query, max_results)

# # daum NewsSearch 클래스 인스턴스 생성
# daum_news_search = NewsSearch(D_Kakao_api_key)
# # daum 뉴스 URL 가져오기
# daum_news_urls = daum_news_search.get_daum_news_urls(query, max_results)


# # URL을 1묶음당 10개씩 정리
# N_organized_data = NewsSearch.organize_urls(naver_news_urls)
# D_organized_data = NewsSearch.organize_urls(daum_news_urls)

# # 결과를 JSON 파일로 저장
# NewsSearch.save_to_json(N_organized_data)
# NewsSearch.save_to_json(D_organized_data)

# pprint(D_organized_data)


import os
import asyncio
from dotenv import load_dotenv
from news_search import NewsSearch
from pprint import pprint

# .env 파일에서 환경 변수를 로드
load_dotenv()

# 네이버와 카카오 API 자격증명
N_Client_ID = os.getenv("N_Client_ID")
N_Client_Secret = os.getenv("N_Client_Secret")
D_Kakao_api_key = os.getenv("D_Kakao_api_key")

# 검색어와 최대 결과 수 설정
query = "비트코인"
max_results = 1000  # 최대 1000개의 결과 가져오기

async def main():
    # NewsSearch 클래스 인스턴스 생성
    news_search = NewsSearch(N_Client_ID, N_Client_Secret, D_Kakao_api_key)

    # 비동기로 네이버와 카카오 뉴스 URL 가져오기
    naver_news_urls_task = news_search.get_naver_news_urls(query, max_results)
    #daum_news_urls_task = news_search.get_daum_news_urls(query, max_results)

    naver_news_urls, daum_news_urls = await asyncio.gather(naver_news_urls_task, daum_news_urls_task)

    # URL을 1묶음당 10개씩 정리
    N_organized_data = NewsSearch.organize_urls(naver_news_urls)
    #D_organized_data = NewsSearch.organize_urls(daum_news_urls)

    # 결과를 JSON 파일로 저장
    NewsSearch.save_to_json(N_organized_data, filename="naver_news_urls.json")
    #NewsSearch.save_to_json(D_organized_data, filename="daum_news_urls.json")

    # 결과 출력
    print("Naver News URLs:")
    pprint(N_organized_data)

    #print("\nDaum News URLs:")
    #pprint(D_organized_data)

# 비동기 메인 함수 실행
asyncio.run(main())
