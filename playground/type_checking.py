from functools import wraps
from os import walk
from types import GenericAlias
from typing import Any, Callable, Optional
from playground.exceptions import ConfigTypeError
from tcfg import type_check, Option
from tcfg.type_check import MISSING

def cfg_type(
    func: Callable|None=None,
    *,
    default: Any = MISSING,
):
    """Decorator to convert a class to a configuration class object."""

    def wrapper(wrap: Callable):
        if default != MISSING:
            class CustomTypeDefault:
                default = 0

                def __init__(self, item: Any):
                    self._item_ = item

                def _value_(self) -> Any:
                    return self._item_
                
                def __class_getitem__(cls, __item):
                    if not isinstance(__item, tuple):
                        __item = tuple(__item,)
                    return GenericAlias(cls, *__item)
            return CustomTypeDefault
        else:
            class CustomType:
                default = None

                def __init__(self, item: Any):
                    self._item_ = item

                def _value_(self) -> Any:
                    return self._item_

                def __class_getitem__(cls, __item):
                    if not isinstance(__item, tuple):
                        __item = tuple(__item,)
                    return GenericAlias(cls, *__item)
            return CustomType

    if func is None:
        return wrapper

    return wrapper(func)

@cfg_type(default=0)
def GreaterThan(value: int, min: int = 0) -> int:
    if value <= min:
        raise TypeError(f"Expected value to be greater than {min}; was {value}")
    return value



if __name__ == "__main__":
    # Da' Rules
    # - Unions match any argument
    # - Optional matches one argument or NoneType
    # - Generics have there __args__ compared.
    #     - If named tuple and is GenericAlias then is certain length and each index is compared
    #     - If form of dict then compares key and value
    #     - If named list then all children must match inner type
    #     - If named set then all children must be unique and match inner type
    # - If type then just compare
    # - If PathType then compare if path exists and format string

    # print(type_check(int, 3))
    # print(type_check(PathType[True], "./type_checking.py"))
    # print(type_check(list[int], [2]))
    # print(type_check(tuple[int, int], [3]))
    # print(type_check(set[int], [3, 5, 6, 6]))
    # print(type_check(dict[str, str], {"valid": "valid"}))
    # print(type_check(Option["Dog", "Cat", 3], MISSING))
    # print(type_check(Optional[int], None))
    # print(type_check(int | None, "Invalid"))
    # print(type_check(Any, "Invalid"))
    data: ClassType[3, int] = ClassType([])

