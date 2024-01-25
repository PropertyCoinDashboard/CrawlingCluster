import re
import time
from dataclasses import dataclass, asdict
from parsing.util.util_parser import soup_data


@dataclass
class CoinSymbolSchema:
    """
    Data class for Coin symbol
    """

    coin_symbol: str
    korean_name: str


class CoinSymbolParsingDriver:
    """
    Class for parsing Coin symbol
    """

    def korbit_parsing_page(self, html_data: str) -> list[CoinSymbolSchema]:
        """
        Parse Korbit page
        """
        crypto_list: list[CoinSymbolSchema] = []
        market_data = soup_data(
            html_data=html_data, element="div", elements={"id": "cryptosM"}
        )
        for market_div in market_data:
            for item_div in market_div.find_all(
                "div", {"class": "market-list-items hover:bg-slate-50"}
            ):
                for item in item_div.find_all(
                    "div", {"class": "inline-flex items-center"}
                ):
                    time.sleep(2)
                    coin_symbol_span: str = item_div.find(
                        "span", {"class": "text-slate-400 text-sm"}
                    )
                    data = CoinSymbolSchema(
                        coin_symbol=coin_symbol_span.text,
                        korean_name=item.text,
                    )
                    print(data)
                    crypto_list.append(asdict(data))

        return crypto_list

    def bithum_parsing_page(self, html_data: str) -> list[CoinSymbolSchema]:
        """
        Parse Bithum page
        """
        crypto_list: list[CoinSymbolSchema] = []
        market_data: list = soup_data(
            html_data=html_data,
            element="div",
            elements={"class": "MarketTable_market-wrap-list__2fKBD"},
        )
        for market_div in market_data:
            for row in market_div.find_all(
                "tr", {"class": "MarketRow_market-row__ZzE1-"}
            ):
                time.sleep(2)
                for anchor in row.find_all("a"):
                    for strong in anchor.find_all("strong"):
                        hangle: str = re.sub("[a-zA-z]", "", strong.text)
                        anchor_span = anchor.find(
                            "span", {"class": "MarketRow_sort-coin__aIyw1"}
                        )
                        data = CoinSymbolSchema(
                            coin_symbol=anchor_span.text.split("/")[0],
                            korean_name=hangle.replace(" ", ""),
                        )
                        print(data)
                        crypto_list.append(asdict(data))

        return crypto_list
