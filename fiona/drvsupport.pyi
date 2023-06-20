from fiona.path import UnparsedPath
from typing import (
    Dict,
    Union,
    Any
)


def _driver_converts_field_type_silently_to_str(driver: str, field_type: str) -> bool: ...


def _driver_supports_field(driver: str, field_type: str) -> bool: ...


def _driver_supports_timezones(driver: str, field_type: str) -> bool: ...


def driver_from_extension(path: Union[str, UnparsedPath]) -> str: ...


def vector_driver_extensions() -> Dict[str, str]: ...


def supported_drivers() -> Dict[str, str]: ...


def _driver_supports_mode(driver: Any, mode: Any) -> bool: ...