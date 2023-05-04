from typing import (
    Optional,
    Tuple,
    Union,
)


def parse_paths(
    uri: str,
    vfs: Optional[str] = ...
) -> Union[Tuple[str, str, str], Tuple[str, None, None], Tuple[str, str, None]]: ...


def valid_vsi(vsi: str) -> bool: ...


def vsi_path(path: str, vsi: Optional[str] = ..., archive: None = ...) -> str: ...
