from typing import Type

FIELD_TYPES: list[Type]
FIELD_TYPES_MAP: dict[str, Type]
FIELD_TYPES_MAP_REV: dict[Type, str]


def normalize_field_type(ftype: str) -> str: ...
