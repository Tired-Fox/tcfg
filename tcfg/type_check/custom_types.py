from inspect import getfullargspec
from pathlib import Path
from types import GenericAlias
from typing import Any, Callable, Protocol, TypeVar, runtime_checkable
from .base import MISSING, type_str, get_type
from .exceptions import CustomTypeError, ConfigTypeError

__all__ = [
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
    "PathType",
    "new",
]


@runtime_checkable
class CFGCustomType(Protocol):
    __module__ = 'builtins'
    _default_ = None
    __args__ = ()
    _validator_args_ = []
    _validator_arg_types_ = {}
    _return_anno_ = None
    _vararg_ = False

    def __init__(self, item: Any):
        ...

    @staticmethod
    def _validator_(value, *args) -> Any:
        ...

    def __class_getitem__(cls, __item):
        ...


def new(value: Any) -> Any:
    return value


def custom_type(
    default: Any = MISSING,
):
    """Decorator to convert a class to a configuration class object."""

    def wrapper(wrap: Callable):
        args, varargs, _, _, _, _, annotations = getfullargspec(wrap)

        vararg = None
        if varargs is not None:
            vararg = (varargs, annotations.pop(varargs, MISSING))

        args.remove("value")
        annotations.pop("value")

        class CustomType(Any):
            __module__ = 'builtins'
            _default_ = default
            __args__ = ()
            _validator_args_ = args
            _validator_arg_types_ = {key: annotations[key] for key in args}
            _return_anno_ = annotations.pop("return", None)
            _vararg_ = vararg

            def __init__(self, item: Any):
                self._value_ = item

            @staticmethod
            def _validator_(value, *args) -> Any:
                return wrap(value, *args)

            def __class_getitem__(cls, __item):
                if not isinstance(__item, tuple):
                    __item = (__item,)
                return GenericAlias(cls, __item)

        CustomType.__name__ = wrap.__name__
        CustomType.__qualname__ = wrap.__qualname__
        return CustomType

    return wrapper


class ARG:
    def __init__(self, idx: int):
        self.idx = idx


def ct_value(ct) -> Any:
    """Get the value from the custom type initialization.

    Example:

    @custom_type(default=ARG(0))
    def GreaterThan(value: int, min: int = 0) -> int:
        if value < min:
            raise TypeError("Value was less than the minimum")

    data: GreaterThan[2] = GreaterThan(3)
    """
    if isinstance(ct, CFGCustomType):
        return ct._value_
    raise ValueError("Can only get the custom type value from custom types.")


def ct_validate(ct, value: Any, __parents__: list | None = None) -> Any:
    """Validate a value against a custom type. The arguments are automatically
    validated against their type annotations. If the value is MISSING then a
    default value can be pulled from the specified default, which can be an argument
    to the type, or inferred through the methods return type. If neither is valid then
    None is returned by default.

    To generate a proper ConfigTypeError with full type error hinting, the method needs to
    raise a TypeError with the desired message. The message will be used in a new ConfigTypeError
    and the type error hinting is automatically injected.

    All cases that validate the values type is handled in the wrapped method. Nothing is inferred
    about the value and what it should be. ONLY the args and default value are automatically handled.
    """
    __parents__ = __parents__ or []

    if not hasattr(ct, "_validator_args_"):
        raise ValueError("Can only validate types for custom types")

    # Validate args
    idx = -1
    for arg, targ in zip(ct.__args__, ct._validator_args_):
        idx += 1
        if targ in ct._validator_arg_types_ and not isinstance(arg, ct._validator_arg_types_[targ]):
            raise ConfigTypeError(
                [*__parents__, (ct, idx)],
                f"The type for arg {targ!r} is {type_str(ct._validator_arg_types_[targ])!r},"
                + f" but a value of type {get_type(arg).__name__!r} was found",
            )

    if idx < len(ct._validator_args_) and ct._vararg_ is not None and ct._vararg_[1] != MISSING:
        for i, arg in enumerate(ct.__args__[idx + 1 :]):
            if not isinstance(arg, ct._vararg_[1]):
                raise ConfigTypeError(
                    [*__parents__, (ct, i + idx + 1)],
                    f"The type for the varargs, *{ct._vararg_[0]} is {get_type(ct._vararg_[1]).__name__!r}; found mismatched type {get_type(arg).__name__!r}.",
                )

    # Build default if MISSING
    if value == MISSING:
        try:
            if ct._default_ == MISSING:
                return ct._return_anno_ if ct._return_anno_ is None else ct._return_anno_()
            if isinstance(ct._default_, ARG):
                return ct.__args__[ct._default_.idx]
            return ct._default_
        except:
            return None

    # Call validator method and return it's value or reraise a caught execption
    stop = len(ct._validator_args_) if ct._vararg_ is None else len(ct.__args__)
    try:
        return ct._validator_(value, *ct.__args__[:stop])
    except TypeError as te:
        raise ConfigTypeError([*__parents__, (ct, None)], str(te))
    except CustomTypeError as cte:
        idx = None
        if cte.arg is not None:
            idx = ct._validator_args_.index(cte.arg)
        raise ConfigTypeError([*__parents__, (ct, idx)], cte.message)


@custom_type(default=".")
def PathType(value: str, exists: bool = False, *args: str) -> str:
    if not isinstance(value, str):
        raise TypeError(f"Expected value to be 'str'; was {get_type(value).__name__!r}")

    value = value.replace("\\", "/").replace("//", "/").lstrip("./")
    if exists and not Path(value).exists():
        raise CustomTypeError(
            f"File not found at location \x1b[32m{value!r}\x1b[39m. "
            + "Either create the path or change the path value",
            arg="exists",
        )

    return value


@custom_type(default=ARG(0))
def GreaterThan(value: int, min: int = 0):
    if not isinstance(value, int):
        raise TypeError(f"Expected value to be 'int'; was {get_type(value).__name__!r}")

    if value <= min:
        raise TypeError(f"Expected value to be greater than {min}; was {value}")

    return value


@custom_type(default=ARG(0))
def LessThan(value: int, max: int = 0):
    if not isinstance(value, int):
        raise TypeError(f"Expected value to be 'int'; was {get_type(value).__name__!r}")

    if value >= max:
        raise TypeError(f"Expected value to be less than {max}; was {value}")

    return value


@custom_type(default=ARG(0))
def Range(value: int, min: int = 0, max: int = 0):
    if not isinstance(value, int):
        raise TypeError("Expected value to be an int")

    if value < min or value >= max:
        raise TypeError(f"Expected {min} <= value < {max}; but was {value}")

    return value
