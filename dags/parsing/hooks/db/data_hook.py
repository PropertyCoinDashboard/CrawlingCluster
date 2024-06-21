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

    okt_pos: list | list[tuple[str]] = okt.pos(text, norm=True, stem=True)

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
        title: str,
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
        self.title = title
        self.text = text
        self.keyword = keyword
        self.keyword_coin = set(["비트코인", "비트", "코인", "리플", "BTC", "btc"])
        self.keyword_other = set(["채굴", "화폐", "가상화폐", "달러"])
        self.cleaned_text = self._clean_text()
        self.present_time = present_time_str
        self.okt = Okt()

    def _clean_text(self) -> list[str]:
        """문장 당 30자 이하 필터링"""
        sentences = self.text.split(",")
        return [
            sentence
            for sentence in sentences
            if (
                len(sentence.strip()) <= 30
                and (
                    any(keyword in sentence for keyword in self.keyword_coin)
                    or any(keyword in sentence for keyword in self.keyword_other)
                )
            )
            or len(sentence.strip()) > 30
        ]

    def _join_sentences(self, sentences: list[str]) -> str:
        """필터링한 URL 합치기"""
        return " ".join(sentences)

    def __len__(self) -> int:
        """길이 계산"""
        return len(self._join_sentences(self.cleaned_text))

    def calculate_frequencies(self) -> list[tuple[str, float]]:
        """제일 많이 나온 단어가 text에서 몇퍼센트의 비율을 차지하는지"""
        try:
            total_sentences: int = self.__len__()
            frequencies = list(
                map(
                    lambda x: (x[0], min(round(x[1] / total_sentences * 100, 2), 1.0)),
                    (
                        filter(lambda x: x == self.keyword[0], [self.keyword[0]])
                        if self.keyword
                        else []
                    ),
                )
            )

            return frequencies
        except ZeroDivisionError:
            frequencies = (self.keyword[0][0], 0)
            return frequencies

    def time_cal(self) -> int:
        """시간 계산"""
        present_time_str = self.present_time.replace(": ", " ")
        present_date = datetime.strptime(present_time_str, "%Y-%m-%d %H:%M:%S")
        present_date = int(present_date.strftime("%Y%m%d"))
        return present_date

    def calculate_target(self) -> float:
        """계산 로직"""

        def target_score(freq_value: str, target: float) -> float:
            if freq_value in self.keyword_coin:
                target += 0.4
            elif freq_value in self.keyword_other:
                target += 0.2
            else:
                target -= 0.2
            return target

        present_time = datetime.now(pytz.timezone("Asia/Seoul")).date()
        present_time_int = int(present_time.strftime("%Y%m%d"))

        new_time: int = self.time_cal()

        target = 0.4  # 기본 점수 설정을 낮춤

        if any(keyword in self.title for keyword in self.keyword_coin):
            target += 0.1

        for frequency in self.calculate_frequencies():
            print(frequency)
            freq_value, freq_score = frequency

            if isinstance(freq_score, float):
                length: int = self.__len__()
                if (2000 <= length <= 10000) and (0.25 <= freq_score <= 0.9):
                    target = target_score(freq_value, target)

        adjustments = {0: 0, 2: -0.1, 3: -0.2, 4: -0.3}
        difference = present_time_int - new_time
        target += adjustments.get(difference, -0.4)

        # 최대 1점을 넘지 않도록 조정
        if target > 1.0:
            target = 1.0
        if target <= 0:
            target = 0
            return target

        return round(target, 2)
