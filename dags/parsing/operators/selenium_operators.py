from parsing.util._typing import UrlCollect

from airflow.models import BaseOperator
from airflow.utils.decorators import apply_defaults

from parsing.protocol import CrawlingProcess


class NaverCrawlingOperator(BaseOperator):
    @apply_defaults
    def __init__(self, count: int, target: str, site: str, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.count = count
        self.target = target
        self.site = site

    def selenium_google(self) -> UrlCollect:
        return CrawlingProcess(self.target, self.count).process_google_selenium()

    def selenium_bing(self) -> UrlCollect:
        return CrawlingProcess(self.target, self.count).process_bing_selenium()

    # fmt: off
    def execute(self, context) -> list[list[str]]:
        if self.site == "google_s":
            result = self.selenium_google()
        elif self.site == "bing_s":
            result = self.selenium_bing()
        else:
            raise ValueError("Invalid site specified")

        data = [i for i in result]
        return data
