from fiona.crs import CRS
from fiona.model import Geometry
from typing import (
    Dict,
    List,
    Optional,
    Tuple,
    Union,
)


def transform(
    src_crs: Union[Dict[str, Union[str, bool]], Dict[str, str], str],
    dst_crs: Union[Dict[str, Union[str, bool]], Dict[str, str], str],
    xs: List[float],
    ys: List[float]
) -> Tuple[List[float], List[float]]: ...


def transform_geom(
    src_crs: Union[Dict[str, Union[str, bool]], CRS, Dict[str, str], str],
    dst_crs: Union[Dict[str, Union[str, bool]], Dict[str, str], str],
    geom: Union[Dict[str, Union[str, List[Dict[str, Union[List[Tuple[float, float]], str]]]]], List[Geometry], Geometry, Dict[str, Union[str, Tuple[Tuple[Tuple[float, float], Tuple[float, float], Tuple[float, float], Tuple[float, float], Tuple[float, float]]]]]],
    antimeridian_cutting: bool = ...,
    antimeridian_offset: float = ...,
    precision: int = ...
) -> Optional[Union[List[Geometry], Geometry]]: ...
