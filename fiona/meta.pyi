from typing import (
    Dict,
    List,
    Optional,
    Union,
)


def _parse_options(xml: str) -> Dict[str, Union[Dict[str, Union[str, List[str]]], Dict[str, str]]]: ...


def dataset_creation_options(driver: str) -> Dict[str, Union[Dict[str, Union[str, List[str]]], Dict[str, str]]]: ...


def dataset_open_options(driver: str) -> Dict[str, Union[Dict[str, Union[str, List[str]]], Dict[str, str]]]: ...


def extension(driver: str) -> Optional[str]: ...


def extensions(driver: str) -> Optional[List[str]]: ...


def layer_creation_options(driver: str) -> Dict[str, Union[Dict[str, Union[str, List[str]]], Dict[str, str]]]: ...


def print_driver_options(driver: str) -> None: ...


def supported_field_types(driver: str) -> Optional[List[str]]: ...


def supported_sub_field_types(driver: str) -> Optional[List[str]]: ...


def supports_vsi(driver: str) -> bool: ...
