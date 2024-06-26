import asyncio
from parsing.util._typing import UrlCollect

from airflow.models import BaseOperator
from airflow.utils.decorators import apply_defaults

from parsing.protocol import CrawlingProcess


class CrawlingOperator(BaseOperator):
    """크롤링 operator"""

    template_fields = ("count", "target")

    @apply_defaults
    def __init__(self, count: int, target: str, site: str, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.count = count
        self.target = target
        self.site = site

    async def naver_again(self) -> UrlCollect:
        print(self.target, self.count)
        return await CrawlingProcess(self.target, self.count).process_naver()

    # fmt: off
    def execute(self, context) -> list[list[str]]:
        loop = asyncio.get_event_loop()
        if self.site == "naver":
            result = loop.run_until_complete(self.naver_again())
        else:
            raise ValueError("Invalid site specified")

        data = [i for i in result]
        return data
