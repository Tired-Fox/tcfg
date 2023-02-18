from functools import cached_property
from typing import Any, Optional

from saimll import SAIML


class Missing:
    pass


MISSING = Missing()


class Options:
    def __init__(self, *options: Any, default: Any = MISSING) -> None:
        self.__options = set()

        for option in options:
            if hasattr(option, "__dataclass_fields__"):
                for value in getattr(option, "__dataclass_fields__").values():
                    self.__options.add(value.default)
            elif not isinstance(option, type):
                self.__options.add(option)
            else:
                raise TypeError(
                    "Options may only be dataclasses, literals, or instances"
                )

        if default is not MISSING:
            if default not in self.__options:
                raise ValueError("Default option value must be in the provided options")
            self.__default = default

    @property
    def default(self) -> Any:
        """The default option."""
        return self.__default

    @property
    def options(self) -> set:
        """The options available."""
        return self.__options

    @cached_property
    def types(self) -> tuple:
        """The different types of options."""
        types = set()
        for val in self.options:
            if isinstance(val, type):
                types.add(val)
            else:
                types.add(type(val))
        return tuple(types)


class TypesDefault:
    """Representation of a values valid types along with it's default value."""

    def __init__(
        self,
        *args: type,
        nested_types: Optional[list] = None,
        default: Any = None,
    ) -> None:
        self.types = tuple(
            val for val in args if not isinstance(val, (TypesDefault, dict))
        )
        self.nested_types = nested_types
        if (
            len(self.types) > 0
            and default is not None
            and not isinstance(default, self.types)
        ):
            raise TypeError(
                SAIML.parse(
                    f"*Default value must one of the valid types \
\\[{', '.join(f'[@F #f5a97f]{val.__name__}[@]' for val in self.types)}\\]"
                )
            )

        if len(args) == 0:
            self.types = (type(default),)

        if isinstance(default, dict):
            self.__default = dict(default)
        elif isinstance(default, list):
            self.__default = list(default)
        elif isinstance(default, tuple):
            self.__default = tuple(default)
        else:
            self.__default = default

    @property
    def default(self) -> Any:
        """The default value of the variable."""
        return self.__default

    def __repr__(self) -> str:
        return (
            f"{' | '.join([t.__name__ for t in self.types])} = {repr(self.__default)}"
        )
