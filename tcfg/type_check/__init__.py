from pathlib import Path
from types import GenericAlias, NoneType, UnionType
from typing import Any, Optional

from .base import (
    Alias,
    SpecialGenericAlias,
    UnionAlias,
    MISSING,
    Missing,
    type_str,
    get_type,
    Option,
    LiteralGenericAlias,
    AnyAlias,
)
from .custom_types import CFGCustomType
from .exceptions import ConfigTypeError, CustomTypeError
from .custom_types import *

__all__ = [
    # To type check a value
    "type_check",
    # Types
    "PathType",
    "MISSING",
    "Option",
    "Optional",
    "Any",
    # Exceptions
    "ConfigTypeError",
    "CustomTypeError",
    # To create new types
    "custom_type",
    "ARG",
    # For getting init value and validating
    "ct_value",
    "ct_validate",
    # pre built custom types
    "Range",
    "GreaterThan",
    "LessThan",
]


def _type_check_union(_type: UnionAlias, _value: Any, __parents__: list | None = None) -> Any:
    __parents__ = __parents__ or []
    if not isinstance(_type, UnionType) and _type.__name__ == "Optional":
        if _value == MISSING:
            return None

        if not isinstance(_value, (_type.__args__[0], NoneType)):
            raise ConfigTypeError(
                [*__parents__, (_type, 0)],
                f"Expected either {type_str(_type.__args__[0])!r} or None; was {get_type(_value).__name__!r}",
            )

        return _value
    else:
        if _value == MISSING:
            return _type.__args__[0]()

        if not isinstance(_value, _type.__args__):
            raise ConfigTypeError(
                [*__parents__, (_type, None)],
                f"Expected on of {', '.join(repr(type_str(arg)) for arg in _type.__args__)}; was {get_type(_value).__name__!r}",
            )

        return _value


def _type_check_list_(_type: Alias, _value: Any, __parents__: list | None) -> Any:
    __parents__ = __parents__ or []

    if _value == MISSING:
        return []
    if not isinstance(_value, list):
        raise ConfigTypeError(
            [*__parents__, (_type, None)], f"Expected a list not a {type_str(get_type(_value))!r}"
        )

    if len(_type.__args__) > 0:
        idx = 0
        try:
            for value in _value:
                _value[idx] = type_check(_type.__args__[0], value, [*__parents__, (_type, 0)])
                idx += 1
        except ConfigTypeError as cte:
            raise ConfigTypeError(
                cte.parents,
                f"list[{idx}]: {cte.message}",
            ) from cte
    return _value


def _type_check_tuple_(_type: Alias, _value: Any, __parents__: list | None) -> Any:
    __parents__ = __parents__ or []

    if _value == MISSING:
        return tuple()
    if not isinstance(_value, (list, tuple)):
        raise ConfigTypeError(
            [*__parents__, (_type, None)],
            f"Expected the value to be a list or tuple not a {type_str(get_type(_value))!r}",
        )

    _value = list(_value)
    if len(_type.__args__) > 0:
        if len(_type.__args__) != len(_value):
            raise ConfigTypeError(
                [*__parents__, (_type, None)],
                f"Expected a list or tuple of size {len(_type.__args__)}; was size {len(_value)}",
            )

        idx = 0
        try:
            for value in _value:
                _value[idx] = type_check(_type.__args__[0], value, [*__parents__, (_type, idx)])
                idx += 1
        except ConfigTypeError as cte:
            raise ConfigTypeError(
                cte.parents,
                f"tuple[{idx}]: {cte.message}"
            ) from cte
    return tuple(_value)


def _type_check_set_(_type: Alias, _value: Any, __parents__: list | None) -> Any:
    __parents__ = __parents__ or []

    if _value == MISSING:
        return set()
    if not isinstance(_value, (list, tuple, set)):
        raise ConfigTypeError(
            [*__parents__, (_type, None)],
            f"Expected the value to be a list, tuple, or set not a {type_str(get_type(_value))!r}",
        )

    _value = list(_value)
    if len(_type.__args__) > 0:
        idx = 0
        try:
            for value in _value:
                _value[idx] = type_check(_type.__args__[0], value, [*__parents__, (_type, 0)])
                idx += 1
        except ConfigTypeError as cte:
            raise ConfigTypeError(
                cte.parents,
                f"set[{idx}]: {cte.message}"
            ) from cte
    return set(_value)


def _type_check_dict_(_type: Alias, _value: Any, __parents__: list | None) -> Any:
    __parents__ = __parents__ or []

    if _value == MISSING:
        return {}

    if not isinstance(_value, dict):
        raise ConfigTypeError(
            [*__parents__, (_type, None)],
            f"Expected the value to be a dict not a {type_str(get_type(_value))!r}",
        )

    if len(_type.__args__) > 0:
        if len(_type.__args__) < 2:
            raise ConfigTypeError(
                [*__parents__, (_type, None)],
                "Expected a type for both key and value. Only found a type for the key",
            )

        for key, value in _value.items():
            key = type_check(_type.__args__[0], key, [*__parents__, (_type, 0)])
            _value[key] = type_check(_type.__args__[1], value, [*__parents__, (_type, 1)])

    return _value


def _type_check_literal_(_type: Alias, _value: Any, __parents__: list | None) -> Any:
    __parents__ = __parents__ or []

    if _value == MISSING:
        return _type.__args__[0]

    if _value not in _type.__args__:
        raise ConfigTypeError(
            [*__parents__, (_type, None)],
            f"Expected one of {', '.join(repr(arg) for arg in _type.__args__)}: was {_value!r}",
        )

    return _value


def _type_check_generic(_type: Alias, _value: Any, __parents__: list | None = None) -> Any:
    __parents__ = __parents__ or []

    name = _type.__name__.rsplit(".", 1)[-1]
    if name in ["list", "List"]:
        return _type_check_list_(_type, _value, __parents__)
    if name in ["tuple", "Tuple"]:
        return _type_check_tuple_(_type, _value, __parents__)
    if name in ["set", "Set"]:
        return _type_check_set_(_type, _value, __parents__)
    if name in ["Dict", "dict"]:
        return _type_check_dict_(_type, _value, __parents__)
    if name in ["Literal"]:
        return _type_check_literal_(_type, _value, __parents__)
    raise TypeError(f"Unkown GenericAlias: {_type}")


def type_check(
    _type: type | UnionAlias | GenericAlias, _value: Any, __parents__: list | None = None
) -> Any:
    """Type check a value agains it's type. The type can be any generic alias, union, or plain type.
    The types are checked recursively with the built-in `isinstance`.

    Args:
        _value (Any): The value to type check.
        _type (type | Union | GenericAlias): The type to type check the value with.

    Raises:
        TypeError: When the value is mismatched from its type. The error message specifies what part of the
        type doesn't match the value.
    """

    __parents__ = __parents__ or []

    if isinstance(_type, CFGCustomType):
        return ct_validate(_type, _value, __parents__)
    if _type is None:
        if _value is not None:
            raise ConfigTypeError(
                [*__parents__, (_type, None)], f"Expected value to be None; was {get_type(_value)}"
            )
        return None
    if isinstance(_type, AnyAlias):
        if _value == MISSING:
            return None
        return _value
    if isinstance(_type, UnionAlias):
        return _type_check_union(_type, _value, __parents__)
    if isinstance(_type, (GenericAlias, SpecialGenericAlias, LiteralGenericAlias)):
        return _type_check_generic(_type, _value, __parents__)
    if isinstance(_type, type):
        if _value == MISSING:
            try:
                return _type()
            except:
                return None

        if not isinstance(_value, _type):
            raise ConfigTypeError(
                [*__parents__, (_type, None)],
                f"Expected {_type.__name__!r} but was {type(_value).__name__!r}",
            )

        return _value

    raise TypeError(f"Unkown type for type check: {_type}")
