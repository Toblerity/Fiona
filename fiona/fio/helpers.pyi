from click.testing import _NamedTextIOWrapper
from typing import (
    Any,
    Dict,
    Iterator,
    List,
    Optional,
    Tuple,
    Union,
)
from fiona.model import Geometry


def eval_feature_expression(
    feature: Dict[str, Union[Dict[str, Union[str, List[List[List[float]]]]], str, Dict[str, Optional[Union[float, str, int]]]]],
    expression: str
) -> Union[float, bool]: ...


def make_ld_context(context_items: Tuple[str]) -> Dict[str, Union[Dict[str, Union[str, Dict[str, str]]], str]]: ...


def obj_gen(lines: _NamedTextIOWrapper, object_hook: None = ...) -> Iterator[Any]: ...


RecRoundObj = Union[Geometry, int, float, List[Union[Geometry, int, float]]]
def recursive_round(obj: RecRoundObj, precision: float) -> RecRoundObj: ...