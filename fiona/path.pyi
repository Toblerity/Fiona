from typing import Union


def parse_path(
    path: Union[UnparsedPath, str, ParsedPath]
) -> Union[UnparsedPath, ParsedPath]: ...


def vsi_path(path: Union[UnparsedPath, ParsedPath]) -> str: ...


class ParsedPath:
    @classmethod
    def from_uri(cls, uri: str) -> ParsedPath: ...
    @property
    def is_local(self) -> bool: ...


class UnparsedPath:
    @property
    def name(self) -> str: ...
