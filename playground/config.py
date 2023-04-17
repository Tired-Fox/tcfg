"""
Generate configuration objects with eaze. Why inheritance? Using inheritance
allows for intellisense
and better editor support while using the configuration objects.

Features:
- You can have nested configuration objects
- configuration objects that load data from different files
- different configuration file types; yml, json, and toml by default
- Each configuration object can load configurations from different file types
- Extensible with more config types. All you need to do is add load and save
methods to the class
for the given file extension. Example; `cfg.ini` would need a `load_ini` and a
`save_ini` added
to the class. The parent `cfg` class automatically calls these methods to get
the dict
representation of the parsed file and to save a string of the config dict back
to the file.
- reserved `_path` variable that specifies where the configuration file is
located
"""
from __future__ import annotations

from inspect import getmembers, ismethod

from pathlib import Path
from typing import (
    Callable,
    Generic,
    Iterable,
    Iterator,
    Protocol,
    Type,
    TypeVar,
    get_type_hints,
    Any,
)

# PARSERS
from json import loads as json_load, dumps as json_dump

# !TODO: wall this behind a features
try:
    from toml import loads as toml_load, dumps as toml_dump
except:

    def toml_load(*args, **kwargs):
        raise ValueError("The toml module must be installed before it can be used.")

    def toml_dump(*args, **kwargs):
        raise ValueError("The toml module must be installed before it can be used.")


try:
    from yaml import safe_load as yml_load, dump as yml_dump
except:

    def yml_load(*args, **kwargs):
        raise ValueError("The PyYaml module must be installed before it can be used.")

    def yml_dump(*args, **kwargs):
        raise ValueError("The PyYaml module must be installed before it can be used.")


from saimll import ppath

# ? CONFIG LOGIC
from tcfg.type_check import Missing, MISSING, type_check, ConfigTypeError, Option, PathType, new


class ConfigKeyError(Exception):
    pass


def setup_default(default: Any):
    """Create copies of dict, list, tuple, and set. Return passed value
    otherwise.
    """
    if isinstance(default, (dict, list, tuple, set)):
        return type(default)(default)
    return default


def get_default(_type):
    try:
        if cfg not in _type.__bases__:
            return _type()
    except:
        return None


class ConfigError(Exception):
    pass


class cfg:
    """Base typed config class."""

    _path_: str | Missing = ""
    """Path to where the configs save file is located."""

    __tcfg_strict__: bool = True
    """Whether to throw errors if there are config values found that are not
    defined.
    """

    __tcfg_values__: dict[str, dict] = {}
    """The found and compiled class attributes for the configuration.

    Template:
        {
            'data': {
                'type': CFGType | CFGUnionType | CFGGenericAlias,
                'default': Any
            },
            ...
        }
    """

    def __init__(
        self,
        data: dict | None = None,
        parents: list[str] | None = None,
        *,
        strict: bool = True,
        skip_invalid: bool = False,
    ) -> None:
        cfg.__tcfg_setup__(self)

        self.__tcfg_strict__ = strict
        self.__tcfg_skip_invalid__ = skip_invalid

        if self._path_ != MISSING:
            data = self._parse_file_(data)
        else:
            data = data or {}

        parents = parents or []
        if self._path_ != MISSING and len(parents) == 0:
            parents.append(repr(self._path_))
        self.__validate__(data, parents)

    def __call__(
        self,
        data: dict | None = None,
        parents: list[str] | None = None,
        *,
        strict: bool = True,
        skip_invalid: bool = False,
    ):
        self.__init__(data, parents, strict=strict, skip_invalid=skip_invalid)

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
                __tcfg_values__[i[0]] = {"type": MISSING, "default": setup_default(i[1])}

        # Get annotations for class attributes
        for anno, _type in self.__annotations__.items():
            if not anno.startswith("_"):
                if anno not in __tcfg_values__:
                    __tcfg_values__[anno] = {"type": MISSING, "default": MISSING}
                __tcfg_values__[anno]["type"] = eval(_type )
        # for anno, _type in get_type_hints(type(self)).items():
        #     if not anno.startswith("_"):
        #         if anno not in __tcfg_values__:
        #             __tcfg_values__[anno] = {"type": MISSING, "default": MISSING}
        #         __tcfg_values__[anno]["type"] = _type

        # Create annotations and default values for class attributes
        # They are only created if they are MISSING
        for attr, data in __tcfg_values__.items():
            if data["type"] == MISSING:
                if data["default"] != MISSING:
                    data["type"] = type(data["default"])

            if data["default"] == MISSING:
                if data["type"] == Any:
                    data["default"] = None
                else:
                    data["default"] = get_default(data["type"])

            setattr(self, attr, data["default"])
        setattr(self, "__tcfg_values__", __tcfg_values__)

    def __tcfg_attributes__(self):
        """Parse and normalize tcfg class attributes for a given object."""

        # Normalize the seperators in the _path_ and strip `/` from the ends
        _path_ = (getattr(self, "_path_") or "").replace("\\", "/").replace("//", "/").lstrip("./")
        setattr(self, "_path_", _path_ if _path_ != "" else MISSING)

    def _parse_file_(self, data: dict | None) -> dict:
        # open and parse the config file
        file_path = Path(self._path_.strip("/"))
        if not file_path.is_file():
            return data or {}
        else:
            extension = file_path.suffix.lstrip(".")
            with file_path.open("r", encoding="utf-8") as cfg_file:
                if not hasattr(self, f"load_{extension}"):
                    raise LookupError(
                        f"Load callback for config extensions of \
'.{extension}' not found; must have load_{extension} defined to load \
'.{extension}' files"
                    )

                if not ismethod(getattr(self, f"load_{extension}")):
                    raise TypeError(f"load_{extension} must be a method")

                text = cfg_file.read()
                return getattr(self, f"load_{extension}")(text) or {}

    def __validate__(self, data: dict, parents: list[str] | None = None):
        """Validate the values from the configuration dict and set the values
        accordingly.
        """
        parents = parents or []

        if not isinstance(data, dict):
            raise TypeError(f"Can not validate configuration of type {type(data).__name__!r}")

        for key, value in data.items():
            if key not in self.__tcfg_values__ and self.__tcfg_strict__:
                raise ConfigKeyError(
                    f"{ppath(*parents, spr='.')}.\x1b[31m{key}\x1b[39m; invalid configuration key {key!r}"
                )

            if (
                not hasattr(self.__tcfg_values__[key]["type"], "__bases__")
                or cfg not in self.__tcfg_values__[key]["type"].__bases__
            ):
                try:
                    result = type_check(self.__tcfg_values__[key]["type"], value)
                    setattr(self, key, result)
                except ConfigTypeError as cte:
                    path = ppath(*parents, clr='white', spr='.')
                    cte.message = f"\n\n\x1b[1m{path}.\x1b[31m{key}\x1b[22;39m: " + cte.message
                    raise cte

        for key, value in self.__tcfg_values__.items():
            if hasattr(value["type"], "__bases__") and cfg in value["type"].__bases__:
                # Init an validate sub config class
                if attr := getattr(self, key) is None or cfg not in attr.__bases__:
                    setattr(
                        self,
                        key,
                        value["type"](data.pop(key, {}), [*parents, key]),
                    )
                else:
                    raise ValueError("Nested config classes should not be initialized. ONLY typed")
            elif getattr(self, key) == MISSING:
                # Assign default value
                try:
                    setattr(self, key, value["type"]())
                except:
                    setattr(self, key, None)

    def __iter__(self) -> Iterator[tuple[str, Any]]:
        for key, value in self.__tcfg_values__.items():
            value = getattr(self, key)
            if isinstance(value, cfg):
                yield key, dict(value)
            else:
                yield key, value

    def as_dict(self) -> dict:
        """Get the dict representation of the full configuration object."""
        result = {}
        for key in self.__tcfg_values__:
            value = getattr(self, key)
            if isinstance(value, cfg):
                result[key] = value.as_dict()
            else:
                result[key] = value
        return result

    def __tcfg_build_save_dict__(self, defaults: bool) -> dict:
        results = {}

        for key, value in self.__tcfg_values__.items():
            cfg_value = getattr(self, key)
            if isinstance(cfg_value, cfg):
                try:
                    # Try saving to specified file
                    cfg_value.save(defaults)
                except Exception:
                    # get save dict and append to current result
                    result = cfg_value.__tcfg_build_save_dict__(defaults)
                    if len(result) > 0:
                        results[key] = result
            else:
                # If not default value then add to results
                if value["default"] != cfg_value or defaults:
                    results[key] = cfg_value

        return results

    def save(self, defaults: bool = False):
        """Save the current configuration data to the configuration files."""

        save_data = self.__tcfg_build_save_dict__(defaults)
        file_path = Path(self._path_)

        extension = file_path.suffix.lstrip(".")
        with file_path.open("+w", encoding="utf-8") as cfg_file:
            if not hasattr(self, f"save_{extension}"):
                raise LookupError(
                    f"Save callback for config extensions of '.{extension}' \
not found; must have save_{extension} defined to save '.{extension}' files"
                )

            if not ismethod(getattr(self, f"save_{extension}")):
                raise TypeError(f"save_{extension} must be a method")

            cfg_file.write(getattr(self, f"save_{extension}")(save_data))

    def load_json(self, data: str) -> dict:
        """Load a json string into a dict."""
        return json_load(data)

    def load_toml(self, data: str) -> dict:
        """Load a toml string into a dict."""
        return toml_load(data)

    def load_yml(self, data: str) -> dict:
        """Load a yaml string into a dict."""
        return self.load_yaml(data)

    def load_yaml(self, data: str) -> dict:
        """Load a yaml string into a dict."""
        return yml_load(data)

    def save_json(self, data: dict) -> str:
        """Save a dict into a json string."""
        return json_dump(data, indent=2)

    def save_toml(self, data: dict) -> str:
        """Save a dict into a toml string."""
        return toml_dump(data)

    def save_yml(self, data: dict) -> str:
        """Save a dict into a yaml string."""
        return self.save_yaml(data)

    def save_yaml(self, data: dict) -> str:
        """Save a dict into a yaml string."""
        return yml_dump(data)


if __name__ == "__main__":

    class Server(cfg):
        port: int = 3031
        host: Option["localhost"] = "localhost"
        watch: list[PathType] = new(["."])
        open: bool = False

    class Config(cfg):
        _path_ = "sample.yml"

        server: Server
        ignore: list[str]
        root: str

    config = Config()
    url = f"http://{config.server.host}:{config.server.port}/{config.root}"
    if config.server.open:
        print("Opening local server at:", url)
    else:
        print("Server started at:", url)

    print("Watching paths:")
    for path in config.server.watch:
        print(f" - {path!r}")

    print("Ignoring any path with:", config.ignore)

