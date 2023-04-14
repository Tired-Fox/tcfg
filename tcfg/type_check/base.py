from types import GenericAlias, UnionType
from typing import Any, Literal, TypeAlias


from typing import _UnionGenericAlias, _SpecialGenericAlias, _LiteralGenericAlias, _AnyMeta

UnionAlias: TypeAlias = _UnionGenericAlias | UnionType
SpecialGenericAlias: TypeAlias = _SpecialGenericAlias
LiteralGenericAlias: TypeAlias = _LiteralGenericAlias
AnyAlias: TypeAlias = _AnyMeta

Alias = GenericAlias | SpecialGenericAlias | LiteralGenericAlias
Type = type | Alias | UnionAlias

class Missing():
    def __bool__(self):
        return False
    def __str__(self):
        return "MISSING"
    def __repr__(self):
        return "MISSING"

MISSING = Missing()

Option = Literal

def type_str(_type) -> str:
    if isinstance(_type, type):
        return _type.__name__
    return str(_type)

def get_type(value: Any) -> type:
    if isinstance(value, type):
        return value
    return type(value)
