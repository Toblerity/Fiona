from click.core import (
    Context,
    Option,
)
from click.decorators import FC
from typing import (
    DefaultDict,
    Dict,
    List,
    Optional,
    Tuple,
    Union,
    Callable,
)


def cb_key_val(ctx: Context, param: Option, value: Union[Tuple[str], Tuple[()]]) -> Dict[str, str]: ...


def cb_layer(ctx: Context, param: Option, value: Optional[str]) -> Optional[Union[str, int]]: ...


def cb_multilayer(
    ctx: Context,
    param: Option,
    value: Union[Tuple[str], Tuple[()]]
) -> DefaultDict[str, List[str]]: ...


def validate_multilayer_file_index(files: Tuple[str], layerdict: DefaultDict[str, List[str]]) -> None: ...


src_crs_opt: Callable[[FC], FC]
dst_crs_opt: Callable[[FC], FC]
creation_opt: Callable[[FC], FC]
open_opt: Callable[[FC], FC]
