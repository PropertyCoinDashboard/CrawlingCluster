from parsing.util.search import AsyncWebCrawler
from konlpy.tag import Okt
from collections import Counter
import csv
import time
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
