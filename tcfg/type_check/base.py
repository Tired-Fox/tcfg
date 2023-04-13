from types import GenericAlias, UnionType
from typing import Any, Literal, TypeAlias


from typing import _UnionGenericAlias, _SpecialGenericAlias, _LiteralGenericAlias, _AnyMeta

UnionAlias: TypeAlias = _UnionGenericAlias | UnionType
SpecialGenericAlias: TypeAlias = _SpecialGenericAlias
LiteralGenericAlias: TypeAlias = _LiteralGenericAlias
AnyAlias: TypeAlias = _AnyMeta

Alias = GenericAlias | SpecialGenericAlias | LiteralGenericAlias
Type = type | Alias | UnionAlias

class Missing(): pass
MISSING = Missing()

Option = Literal

def type_str(_type) -> str:
    if isinstance(_type, type):
        return _type.__name__
    return str(_type)

class PathType(str):
    __args__ = (False,)

    @staticmethod
    def create(value: Any = MISSING):
        if value == MISSING:
            return "."
        return str(value).replace("\\", "/").replace("//", "/")

    def __class_getitem__(cls, __item: bool) -> GenericAlias:
        if not isinstance(__item, bool):
            raise TypeError(
                "PathType may only take one bool literal for typing; PathType[False]."
                + " This value represents whether the file should exist"
            )

        return GenericAlias(PathType, __item)

def get_type(value: Any) -> type:
    if isinstance(value, type):
        return value
    return type(value)
