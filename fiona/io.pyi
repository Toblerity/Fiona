from io import BufferedReader
from fiona.collection import Collection
from fiona.crs import CRS
from typing import (
    Any,
    List,
    Optional,
    Union,
)


class MemoryFile:
    def __enter__(self) -> Union[MemoryFile, ZipMemoryFile]: ...
    def __exit__(self, *args, **kwargs) -> None: ...
    def __init__(
        self,
        file_or_bytes: Optional[Union[bytes, BufferedReader]] = ...,
        filename: Optional[str] = ...,
        ext: str = ...
    ) -> None: ...
    def listdir(self, path: None = ...) -> List[str]: ...
    def listlayers(self, path: None = ...) -> List[str]: ...
    def open(
        self,
        mode: Optional[str] = ...,
        driver: Optional[str] = ...,
        schema: Optional[Any] = ...,
        crs: Optional[CRS] = ...,
        encoding: None = ...,
        layer: Optional[str] = ...,
        vfs: None = ...,
        enabled_drivers: None = ...,
        crs_wkt: Optional[str] = ...,
        allow_unsupported_drivers: bool = ...,
        **kwargs
    ) -> Collection: ...


class ZipMemoryFile:
    def __init__(self, file_or_bytes: Optional[bytes] = ..., filename: Optional[str] = ..., ext: str = ...) -> None: ...
    def open(
        self,
        path: Optional[str] = ...,
        driver: None = ...,
        encoding: None = ...,
        layer: None = ...,
        enabled_drivers: None = ...,
        allow_unsupported_drivers: bool = ...,
        **kwargs
    ) -> Collection: ...
