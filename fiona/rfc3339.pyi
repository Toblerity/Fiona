from re import Match
from typing import (
    Tuple,
    Union,
)


def parse_date(text: str) -> Tuple[int, int, int, int, int, int, int, None]: ...


def parse_datetime(
    text: str
) -> Union[Tuple[int, int, int, int, int, int, int, float], Tuple[int, int, int, int, int, int, int, None], Tuple[int, int, int, int, int, int, int, int]]: ...


def parse_time(
    text: str
) -> Union[Tuple[int, int, int, int, int, int, int, float], Tuple[int, int, int, int, int, int, int, None], Tuple[int, int, int, int, int, int, int, int]]: ...


class group_accessor:
    def __init__(self, m: Match) -> None: ...
    def group(self, i: int) -> Union[int, str]: ...
