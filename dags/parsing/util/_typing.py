from typing import TypedDict, Deque, Callable

UrlCollect = Deque[list[str]]
SeleniumUrlCollect = Callable[[str, int], UrlCollect]


class InnerData(TypedDict):
    values: list[str]


class OuterData(TypedDict):
    inner_dict: dict[int, InnerData]


class UrlDataStructure(TypedDict):
    outer_dict: dict[int, OuterData]


class DataStructure(TypedDict):
    outer_dict: dict[int, dict[int, list]]
