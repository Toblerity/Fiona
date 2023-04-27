from fiona.crs import CRS
from fiona.model import Feature
from fiona.ogrext import (
    ItemsIterator,
    Iterator,
    KeysIterator,
)
from fiona.path import (
    ParsedPath,
    UnparsedPath,
)
from typing import (
    Any,
    Dict,
    List,
    Optional,
    Set,
    Tuple,
    Union,
)


def _get_valid_geom_types(schema: Dict[str, Any], driver: str) -> Set[str]: ...


def get_filetype(bytesbuf: bytes) -> str: ...


class BytesCollection:
    def __init__(self, bytesbuf: Union[bytes, str], **kwds) -> None: ...
    def __repr__(self) -> str: ...
    def close(self) -> None: ...


class Collection:
    def __contains__(self, fid: int) -> bool: ...
    def __del__(self) -> None: ...
    def __enter__(self) -> Union[Collection, BytesCollection]: ...
    def __exit__(self, type: None, value: None, traceback: None) -> None: ...
    def __getitem__(self, item: Union[int, slice]) -> Union[Feature, List[Feature]]: ...
    def __init__(
        self,
        path: Union[UnparsedPath, int, str, ParsedPath],
        mode: Union[int, str] = ...,
        driver: Optional[Union[str, int]] = ...,
        schema: Optional[Any] = ...,
        crs: Optional[Any] = ...,
        encoding: Optional[Union[str, int]] = ...,
        layer: Optional[Union[str, int, float]] = ...,
        vsi: Optional[str] = ...,
        archive: Optional[int] = ...,
        enabled_drivers: Optional[List[str]] = ...,
        crs_wkt: Optional[str] = ...,
        ignore_fields: Optional[Union[List[int], List[str]]] = ...,
        ignore_geometry: bool = ...,
        include_fields: Optional[Union[Tuple[()], List[str]]] = ...,
        wkt_version: Optional[str] = ...,
        allow_unsupported_drivers: bool = ...,
        **kwargs
    ) -> None: ...
    def __iter__(self) -> Iterator: ...
    def __len__(self) -> int: ...
    def __next__(self) -> Feature: ...
    def __repr__(self) -> str: ...
    def _check_schema_driver_support(self) -> None: ...
    @property
    def bounds(self) -> Tuple[float, float, float, float]: ...
    def close(self) -> None: ...
    @property
    def closed(self) -> bool: ...
    @property
    def crs(self) -> Optional[CRS]: ...
    @property
    def crs_wkt(self) -> str: ...
    @property
    def driver(self) -> Optional[str]: ...
    def filter(self, *args, **kwds) -> Iterator: ...
    def flush(self) -> None: ...
    def get(self, item: int) -> Feature: ...
    def get_tag_item(self, key: str, ns: Optional[str] = ...) -> Optional[str]: ...
    def guard_driver_mode(self) -> None: ...
    def items(self, *args, **kwds) -> ItemsIterator: ...
    def keys(self, *args, **kwds) -> KeysIterator: ...
    @property
    def meta(self) -> Dict[str, Union[str, Dict[str, Union[str, Dict[str, str]]], CRS]]: ...
    @property
    def schema(self) -> Any: ...
    def tags(self, ns: Optional[str] = ...) -> Dict[str, str]: ...
    def update_tag_item(self, key: str, tag: str, ns: Optional[str] = ...) -> int: ...
    def update_tags(self, tags: Dict[str, str], ns: Optional[str] = ...) -> int: ...
    def validate_record(self, record: Dict[str, Dict[str, Union[str, Tuple[float, float]]]]) -> bool: ...
    def validate_record_geometry(self, record: Dict[str, Dict[str, Union[str, Tuple[float, float]]]]) -> bool: ...
    def write(
        self,
        record: Union[Feature, Dict[str, Union[str, Dict[str, Union[str, Tuple[int, int]]], Dict[str, str]]]]
    ) -> None: ...
    def writerecords(self, records: Any) -> None: ...
