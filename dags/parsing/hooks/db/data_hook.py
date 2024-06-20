import csv
import pytz
import time
from collections import Counter
from datetime import datetime

from konlpy.tag import Okt
from parsing.util.search import AsyncWebCrawler
from airflow.providers.amazon.aws.hooks.s3 import S3Hook
from airflow.providers.mysql.hooks.mysql import MySqlHook


def data_list_change(**context) -> list[str]:
    url = context["ti"].xcom_pull(key="return_value")
    data_compre: list[str] = [str(*url[i]) for i in range(len(url))]
    return data_compre


async def deep_crawling_run(**context) -> dict[str, set[str]]:
    url = context["ti"].xcom_pull(key="return_value")
    data = [await AsyncWebCrawler(i, 1, 1).run() for i in url]

    context["ti"].xcom_push(key="asnyc_deep", value=data)


def preprocessing(**context) -> list[list[str]]:
    url = context["ti"].xcom_pull(key="asnyc_deep")
    return [first_dict[second] for first_dict in url for second in first_dict]


def keword_preprocessing(text: str) -> list[tuple[str, int]]:
    okt = Okt()

    okt_pos = okt.pos(text, norm=True, stem=True)

    # fmt: off
    str_preprocessing = list(filter(lambda data: data if data[1] in "Noun" else None, okt_pos))
    word_collect = [i[0] for i in str_preprocessing if len(i[0]) > 1]
    word_count = Counter(word_collect).most_common(3)
    return word_count


def extract_mysql_data_to_s3() -> None:
    bucket_name = "sky-burket-test-injection"

    # MySQL configuration
    mysql_hook = MySqlHook(mysql_conn_id="mysql_my_test")
    qs = "SELECT * FROM dash.log;"
    results = mysql_hook.get_records(sql=qs)

    localfile_name = "order_extract_log.csv"
    with open(localfile_name, "w") as fp:
        csv_w = csv.writer(fp, delimiter=",")
        csv_w.writerows(results)
        fp.close()

    timestr = time.strftime("%Y%m%d-%H%M%S")

    out_file_name = f"access_log_{timestr}.csv"

    s3_hook = S3Hook(aws_conn_id="your_aws_connection_id")
    s3_hook.load_file(
        filename=localfile_name, key=out_file_name, bucket_name=bucket_name
    )


class KeywordExtractor:
    """계산하는 로직"""

    def __init__(
        self,
        url: str,
        text: str,
        keyword: list[tuple[str, int]],
        present_time_str: datetime,
    ) -> None:
        """

        Args:
            url (str): url
            text (str): text 원문
            keyword (list[tuple[str, int]]): 단어 빈도 수
            present_time_str (datetime): 현재 날짜
        """
        self.url = url
        self.text = text
        self.keyword = keyword
        self.cleaned_text = self._clean_text()
        self.present_time = present_time_str
        self.okt = Okt()

    def _clean_text(self) -> list[str]:
        """문장 당 30자 이하 필터링"""
        sentences = self.text.split(".")
        return [sentence for sentence in sentences if len(sentence) > 30]

    def _join_sentences(self, sentences: list[str]) -> str:
        """필터링한 URL 합치기"""
        return " ".join(sentences)

    def __len__(self) -> int:
        """길이 계산"""
        return len(self._join_sentences(self.cleaned_text))

    def calculate_frequencies(self) -> list[tuple[str, float]]:
        """제일 많이 나온 단어가 text에서 몇퍼센트의 비율을 차지하는지"""
        try:
            keywords = self.keyword
            total_sentences = len(self.cleaned_text)
            frequencies = [
                (keyword, round((count / total_sentences), 2))
                for keyword, count in keywords
            ]
            return frequencies
        except ZeroDivisionError:
            frequencies = 0
            return frequencies

    def time_cal(self) -> int:
        """시간 계산"""
        present_time_str = self.present_time.replace(": ", " ")
        present_date = datetime.strptime(present_time_str, "%Y-%m-%d %H:%M:%S")
        present_date = int(present_date.strftime("%Y%m%d"))
        return present_date

    def calculate_target(self) -> float:
        """계산 로직"""
        present_time = datetime.now(pytz.timezone("Asia/Seoul")).date()
        present_time_int = int(present_time.strftime("%Y%m%d"))

        new_time = self.time_cal()

        def target_score(freq_value: str, target: float) -> float:
            if freq_value in ["비트코인", "비트", "코인", "리플"]:
                target += 0.4
            elif freq_value in ["채굴", "화폐", "가상화폐", "달러"]:
                target += 0.2
            else:
                target -= 0.2
            return target

        target = 0.4  # 기본 점수 설정을 낮춤
        for frequency in self.calculate_frequencies():
            freq_value = frequency

            if isinstance(freq_value[1], float):
                if self.__len__() > 5300 and freq_value[1] >= 0.35:
                    target = target_score(freq_value[0], target)
                elif self.__len__() > 4500 and freq_value[1] >= 0.35:
                    target = target_score(freq_value[0], target)
                elif self.__len__() > 3500 and freq_value[1] >= 0.45:
                    target = target_score(freq_value[0], target)
                elif self.__len__() > 2300 and freq_value[1] >= 0.5:
                    target = target_score(freq_value[0], target)

        if present_time_int == new_time:
            target += 0
        elif present_time_int - new_time == 2:
            target -= -0.1
        elif present_time_int - new_time == 3:
            target -= -0.2
        elif present_time_int - new_time == 4:
            target -= -0.3
        else:
            target += 0

        # 최대 1점을 넘지 않도록 조정
        if target > 1.0:
            target = 1.0
        if target <= 0:
            target = 0
            return target

        return round(target, 2)
