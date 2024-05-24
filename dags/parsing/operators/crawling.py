import asyncio

from airflow.models import BaseOperator
from airflow.utils.decorators import apply_defaults

from parsing.protocol import CrawlingProcess


class CrawlingOperator(BaseOperator):
    @apply_defaults
    def __init__(self, count: int, target: str, site: str, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.count = count
        self.target = target
        self.site = site

    def execute(self, context) -> list[list[str]]:
        loop = asyncio.get_event_loop()
        if self.site == "naver":
            result = loop.run_until_complete(
                CrawlingProcess(self.target, self.count).process_naver()
            )

        elif self.site == "daum":
            result = loop.run_until_complete(
                CrawlingProcess(self.target, self.count).process_daum()
            )
        else:
            raise ValueError("Invalid site specified")

        data = [i for i in result]
        return data

    async def naver_again(self):
        return await CrawlingProcess(self.target, self.count).process_naver()

    async def daum_again(self):
        return await CrawlingProcess(self.target, self.count).process_daum()
