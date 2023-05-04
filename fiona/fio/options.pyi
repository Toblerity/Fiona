from click.core import (
    Context,
    Option,
)
from typing import (
    DefaultDict,
    Dict,
    List,
    Optional,
    Tuple,
    Union,
)


def cb_key_val(ctx: Context, param: Option, value: Union[Tuple[str], Tuple[()]]) -> Dict[str, str]: ...


def cb_layer(ctx: Context, param: Option, value: Optional[str]) -> Optional[Union[str, int]]: ...


def cb_multilayer(
    ctx: Context,
    param: Option,
    value: Union[Tuple[str], Tuple[()]]
) -> DefaultDict[str, List[str]]: ...


def validate_multilayer_file_index(files: Tuple[str], layerdict: DefaultDict[str, List[str]]) -> None: ...
