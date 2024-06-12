from typing import TypedDict, Deque, Callable

UrlDictCollect = Deque[dict[list[str, str, str]]]

UrlCollect = Deque[list[str]]
ProcessUrlCollect = Callable[[str, int], UrlCollect]


class InnerData(TypedDict):
    values: list[str]


class OuterData(TypedDict):
    inner_dict: dict[int, InnerData]


class UrlDataStructure(TypedDict):
    outer_dict: dict[int, OuterData]


class DataStructure(TypedDict):
    outer_dict: dict[int, dict[int, list]]
