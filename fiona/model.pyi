from __future__ import annotations  # for Python 3.7-3.9

from collections import OrderedDict
from itertools import chain
from typing import (
    Any,
    Dict,
    List,
    Literal,
    Optional,
    Tuple,
    Union,
    Protocol,
)
from typing_extensions import NotRequired, Required, TypedDict  # for Python <3.11 with (Not)Required


def decode_object(obj: Any) -> Union[Dict[str, str], Dict[str, int], Geometry, Feature]: ...


def to_dict(
    val: Dict[str, Union[Dict[str, Union[str, List[List[List[float]]]]], str, Dict[str, Optional[Union[float, str, int]]]]]
) -> Dict[str, Union[Dict[str, Union[str, List[List[List[float]]]]], str, Dict[str, Optional[Union[float, str, int]]]]]: ...


GeoJSONPosition = tuple[float, float] | tuple[float, float, float]
GeoJSONLineStringCoordinateArray = list[GeoJSONPosition]  # two or more positions
GeoJSONLinearRing = list[GeoJSONPosition]  # closed with four or more positions
GeoJSONPolygonCoordinateArray = list[GeoJSONLinearRing]


class GeoJSONPoint(TypedDict):
    type:  Required[Literal["Point"]]
    coordinates: Required[GeoJSONPosition]


class GeoJSONMultiPoint(TypedDict):
    type:  Literal["MultiPoint"]
    coordinates: list[GeoJSONPosition]


class GeoJSONLineString(TypedDict):
    type: Literal["LineString"]
    coordinates: GeoJSONLineStringCoordinateArray


class GeoJSONMultiLineString(TypedDict):
    type: Literal["MultiLineString"]
    coordinates: list[GeoJSONLineStringCoordinateArray]


class GeoJSONPolygon(TypedDict):
    type: Literal["Polygon"]
    coordinates: GeoJSONPolygonCoordinateArray


class GeoJSONMultiPolygon(TypedDict):
    type: Literal["MultiPolygon"]
    coordinates: list[GeoJSONPolygonCoordinateArray]


GeoJSONGeometry = GeoJSONPoint | GeoJSONMultiPoint | GeoJSONLineString | GeoJSONMultiLineString | GeoJSONPolygon | GeoJSONMultiPolygon


class GeoJSONGeometryCollection(TypedDict):
    geometries: list[GeoJSONGeometry]


class GeoJSONFeature(TypedDict):
    type: Literal["Feature"]
    geometry: GeoJSONGeometry | None
    properties: dict | None
    id: NotRequired[str | float]


class GeoJSONFeatureCollection(TypedDict):
    type: Literal["FeatureCollection"]
    features: list[GeoJSONFeature]


class GeoInterface(Protocol):
    @property
    def __geo_interface__(self) -> dict: ...


class Feature:
    def __init__(
        self,
        geometry: Optional[Geometry] = ...,
        id: Optional[Union[int, str]] = ...,
        properties: Optional[Properties] = ...,
        **data
    ) -> None: ...
    @classmethod
    def from_dict(
        cls,
        ob: Optional[Union[Dict[str, object], GeoInterface]] = None,
        **kwargs: Any
    ) -> Feature: ...
    @property
    def geometry(self) -> Optional[Geometry]: ...
    @property
    def id(self) -> Optional[str]: ...
    @property
    def properties(self) -> Union[OrderedDict, Properties]: ...
    @property
    def type(self) -> str: ...


class Geometry:
    @property
    def __geo_interface__(self) -> Dict[str, Union[str, Tuple[int, int]]]: ...
    def __init__(
        self,
        coordinates: Optional[Any] = ...,
        type: Optional[str] = ...,
        geometries: Optional[List[Geometry]] = ...,
        **data
    ) -> None: ...
    @property
    def coordinates(self) -> Any: ...
    @classmethod
    def from_dict(cls, ob: None = ..., **kwargs) -> Geometry: ...
    @property
    def geometries(self) -> Optional[List[Geometry]]: ...
    @property
    def type(self) -> str: ...


class Object:
    def __delitem__(self, key: str) -> None: ...
    def __eq__(self, other: object) -> bool: ...
    def __getitem__(self, item: str) -> Any: ...
    def __init__(self, **kwds) -> None: ...
    def __iter__(self) -> chain: ...
    def __len__(self) -> int: ...
    def __setitem__(self, key: str, value: int) -> None: ...
    def _props(self) -> Dict[str, Any]: ...


class ObjectEncoder:
    def default(self, o: Any) -> Dict[str, Any]: ...


class Properties:
    def __init__(self, **kwds) -> None: ...
    @classmethod
    def from_dict(cls, mapping: None = ..., **kwargs) -> Properties: ...


class _Feature:
    def __init__(
        self,
        geometry: Optional[Geometry] = ...,
        id: Optional[Union[int, str]] = ...,
        properties: Optional[Properties] = ...
    ) -> None: ...


class _Geometry:
    def __init__(
        self,
        coordinates: Optional[Any] = ...,
        type: Optional[str] = ...,
        geometries: Optional[List[Geometry]] = ...
    ) -> None: ...
