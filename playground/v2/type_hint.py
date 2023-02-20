"""S"""
from __future__ import annotations

from inspect import getmembers, ismethod
from types import GenericAlias
from typing import get_type_hints, Any

#? UTILITIES

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

def get_type(value: Any) -> type:
    """Get the type of the value. If it is already a type then the value is returned."""
    if isinstance(value, type):
        return value
    return type(value)

def tcfg_validate_type(_type: type) -> type:
    """Validate the type annotation is one of the valid allowed types."""
    valid_type = (int, float, bool, str, list, dict)
    tcfg_types = (cfg, Path)

    if (
        not isinstance(_type(), tcfg_types)
        and _type not in valid_type
        and not isinstance(_type, GenericAlias)
    ):
        raise TypeError

    if isinstance(_type, GenericAlias):
        input(_type)

    return _type

#? CONFIG LOGIC

class cfg:
    """Base typed config class."""

    _path_: str = ""
    """Path to where the configs save file is located."""

    __tcfg_values__: dict = {}
    """The found and compiled class attributes for the configuration."""

    def __init__(self, data: dict = MISSING) -> None:
        cfg.__tcfg_setup__(self)
        if self._path_ != MISSING:
            # open and parse the config file
            pass
        else:
            if data == MISSING:
                raise Exception("Must provide a path to a config file or a dict to parse")

    def __tcfg_setup__(self):
        __tcfg_values__ = {}

        # Setup default values for cfg class only attributes
        self.__tcfg_attributes__()

        # Get class attribute names and default values
        for i in getmembers(self):
            if (
                not i[0].startswith('_')
                and not ismethod(i[1])
                and i[0] not in ["tcfg_attributes", "tcfg_setup"]
            ):
                __tcfg_values__[i[0]] = {"type": MISSING, "default": i[1]}

        # Get annotations for class attributes
        for anno, _type in get_type_hints(type(self)).items():
            if not anno.startswith("_"):
                if anno not in __tcfg_values__:
                    __tcfg_values__[anno] = {"type": MISSING, "default": MISSING}

                try:
                    _type = tcfg_validate_type(get_type(_type))
                except TypeError as terror:
                    raise TypeError(f"invalid type {get_type(_type)} for attr {anno}") from terror
                __tcfg_values__[anno]["type"] = _type

        # Create annotations and default values for class attributes
        # They are only created if they are MISSING
        for attr, data in __tcfg_values__.items():
            if data["type"] == MISSING:
                data[attr]["type"] = get_type(data["default"])

            if data["default"] == MISSING:
                data["default"] = data["type"]()

            setattr(self, attr, data["default"])

        setattr(self, "__tcfg_values__", __tcfg_values__)

    def __tcfg_attributes__(self):
        """Parse and normalize tcfg class attributes for a given object."""

        # Normalize the seperators in the _path_ and strip `/` from the ends
        _path_ = Path.normalize(getattr(self, "_path_") or "")
        setattr(self, "_path_", _path_ if _path_ != "" else MISSING)

class Nested(cfg):
    """Nested config"""

    _path_ = "nested.json"

    port: int = 8081
    """Port number of the server."""

class Config(cfg):
    """Main config"""

    _path_ = "cfg.json"

    unique: str
    """Unique id of the config."""

    nested: Nested
    """Nested server configurations."""

    extensions: list[str | dict[str, dict]]
    """List of extensions to use for the server."""

    path: Path

# str int float bool list dict
# ? Validat, needs to be one of these types

config = Config()
print(config._path_)
