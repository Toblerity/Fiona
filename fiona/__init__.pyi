from io import (
    BufferedReader,
    BytesIO,
)
from fiona._env import GDALVersion
from fiona.collection import Collection
from fiona.crs import CRS
from fiona.env import Env
from fiona.model import Geometry
from fiona.rfc3339 import FionaDateType

from pathlib import PosixPath
from typing import (
    Any,
    Dict,
    List,
    Optional,
    Tuple,
    Type,
    Union,
)

gdal_version: GDALVersion

def bounds(
    ob: Union[Dict[str, Union[str, List[List[List[int]]]]], Geometry, Dict[str, Union[str, List[List[int]]]], Dict[str, Union[Dict[str, Union[str, List[List[List[float]]]]], str, Dict[str, Optional[Union[float, str, int]]]]], Dict[str, Union[str, List[int]]]]
) -> Union[Tuple[int, int, int, int], Tuple[float, float, float, float]]: ...


def drivers(*args, **kwargs) -> Env: ...


def listdir(path: Union[int, str]) -> List[str]: ...


def listlayers(
    fp: Union[BufferedReader, str, int, PosixPath],
    vfs: Optional[Union[str, int]] = ...,
    **kwargs
) -> List[str]: ...


def open(
    fp: Union[BytesIO, str, PosixPath, BufferedReader],
    mode: str = ...,
    driver: Optional[str] = ...,
    schema: Optional[Any] = ...,
    crs: Optional[Union[CRS, Dict[str, Union[str, bool]], Dict[str, Union[int, bool, str]], str]] = ...,
    encoding: Optional[str] = ...,
    layer: Optional[Union[str, int]] = ...,
    vfs: Optional[str] = ...,
    enabled_drivers: Optional[List[str]] = ...,
    crs_wkt: Optional[str] = ...,
    allow_unsupported_drivers: bool = ...,
    **kwargs
) -> Collection: ...


def prop_type(text: str) -> Union[Type[int], Type[float], Type[str], Type[FionaDateType]]: ...


def prop_width(val: str) -> Optional[int]: ...


def remove(
    path_or_collection: Union[Collection, str],
    driver: Optional[str] = ...,
    layer: Optional[Union[str, int]] = ...
) -> None: ...


supported_drivers: Dict[str, str]
