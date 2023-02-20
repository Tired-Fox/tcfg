from __future__ import annotations
from functools import cached_property
from typing import Any

from saimll import p_value, ppath

__all__ = [
    "MISSING",
    "Path",
    "Options"
]

class Missing:
    """Placeholding for missing values. Allows for null values to be represented as literals."""
MISSING = Missing()

class Path:
    """Allows for eazy path generation."""

    def __init__(self, *paths: str, strip: bool = True) -> None:
        self.path = Path.normalize(*paths, strip=strip) if len(paths) > 0 else ""

    @staticmethod
    def normalize(*paths: str, strip: bool = True) -> str:
        """Normalize a path or segments of a path into a consistant path with `\\` replaced with `/`
        and either leading and trailing `/` stripped or left alone.
        """

        if strip:
            return "/".join(path.replace("\\", "/").strip("/") for path in paths)
        return "/".join(
            [
                paths[1].lstrip("/"),
                *[
                    path.replace("\\", "/").strip("/")
                    for path in paths[1:-1]
                ],
                paths[-1].lstrip("/")
            ]
        )

    def __truediv__(self, scalar: Path):
        if isinstance(scalar, Path):
            return Path(self.path.rstrip("/") + "/" + scalar.path.lstrip("/"))
        raise TypeError("Can't divide with values other that 'Path'")

    def __repr__(self) -> str:
        return f"Path({self.path!r})"

    def __str__(self) -> str:
        return self.path

class Options:
    """A collection of valid options for a given configuration key. The config value must be one of
    the given options.
    """

    def __init__(self, *options: Any, default: Any = MISSING) -> None:
        self.__options = set()

        for option in options:
            if hasattr(option, "__dataclass_fields__"):
                for value in getattr(option, "__dataclass_fields__").values():
                    self.__options.add(value.default)
            elif not isinstance(option, type):
                if isinstance(option, (list, tuple, set)):
                    self.__options.update(set(option))
                else:
                    self.__options.add(option)
            else:
                raise TypeError(
                    "Options may only be dataclasses, literals, or instances"
                )

        if default is not MISSING:
            if default not in self.__options:
                raise ValueError("Default option value must be in the provided options")
            self.__default = default
        else:
            self.__default = list(self.__options)[0]

    @property
    def default(self) -> Any:
        """Default value of the configuration option type."""
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

    def validate(self, value: Any, parents: list[str]) -> bool:
        """Validate if a value is one of the options."""
        if value not in self.options:
            raise TypeError(
                f"{ppath(*parents, spr='.')}; invalid option {p_value(value)}, \
expected one of: {', '.join(p_value(option) for option in self.options)}"
            )
