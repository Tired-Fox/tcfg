from __future__ import annotations

import inspect
from io import TextIOWrapper
from json import JSONEncoder, dump as json_dump, load as json_load
from pathlib import Path
from typing import Any, Iterator, Optional, TYPE_CHECKING

from teddecor import TED, p_value

from .types_default import TypesDefault, Options


def _save_to_file(file: str | Path, data: dict):
    with open(file, "+w", encoding="utf-8") as save_file:
        json_dump(data, save_file, indent=2, cls=ConfigJsonEncoder)


def _save_to_open_file(file: TextIOWrapper, data: dict):
    json_dump(data, file, indent=2, cls=ConfigJsonEncoder)


def _path(path: list[str]) -> str:
    """Generate the formatted path to the given variable."""
    return ".".join(f"[@F #eed49f]{TED.escape(val)}[@F]" for val in path)


def _type(val: Any) -> type:
    if not isinstance(val, type):
        return type(val)
    return val


def _all_types(values: Iterator[Any]) -> type:
    types = set()

    if isinstance(values, (tuple, list)):
        for val in values:
            types.add(_type(val))
    elif isinstance(values, dict):
        for val in values.values():
            types.add(_type(val))
    return types


def _inherits_config_base(val) -> bool:
    if isinstance(val, type):
        mro = val.mro()
    else:
        mro = type(val).mro()

    return ConfigBase in mro


class ConfigJsonEncoder(JSONEncoder):
    """JSONEncoder for any class implementing ConfigBase."""

    def default(self, o):
        """Called when encoding objects."""

        if _inherits_config_base(_type(o)):
            if isinstance(o, type):
                return o.init().as_dict()
            return o.as_dict()
        return JSONEncoder.default(self, o)


class ConfigBase: # pylint: disable=too-many-instance-attributes
    """Base class for configuration logic.

    To customize how configs are loaded and saved you may inherit from this class and implement
    `__save__` and `__load__`. `__save__` takes a dict of the data and a file
    as either a str, Path, or TextIOWrapper. `__load__` takes a file as a str, Path, or
    TextIOWrapper and returns the loaded config as a dict. You may change other dunder methods as
    well, but that may break the functionality of the decorator and class.
    """

    def __init__(
        self,
        cls,
        cfg: Optional[dict] = None,
        save: str | Path | None = None,
        load: str | Path | None = None,
        save_defaults: bool = False,
    ):
        self.__tedconfig_attributes__ = {}
        self.__tedconfig_validated__ = []
        self.__classname__ = cls.__name__.lower()
        self.__qualname__ = self.__class__.__qualname__
        self.__tedconfig_save_defaults__ = save_defaults

        if isinstance(cfg, dict):
            self.__tedconfig_config__ = cfg
            self.__tedconfig_load_path__ = load
        elif isinstance(cfg, (str, Path)):
            self.__tedconfig_config__ = None
            self.__tedconfig_load_path__ = Path(cfg).resolve()
        else:
            self.__tedconfig_config__ = None
            self.__tedconfig_load_path__ = load

        self.__tedconfig_save_path__ = save

        for i in inspect.getmembers(cls):
            if not i[0].startswith("_"):
                if not inspect.ismethod(i[1]):
                    var, value = i
                    setattr(self, var, self.__get_default__(value))
                    self.__tedconfig_attributes__[var] = value

        if cfg is not None or self.__tedconfig_load_path__ is not None:
            self.__parse__()

    @classmethod
    def init(cls, cfg: dict | str | Path | None = None):
        """`classmethod`: Initialize the class and run config validation."""

        return cls(cfg)

    def is_default(self, key=None) -> bool:
        """Determine if a specific attribute is the default value."""
        if key is None:
            # Check if entire config object is default
            return all(self.__default__(attr) for attr in self.__tedconfig_attributes__)

        if key in self.__tedconfig_attributes__:
            # Check if specific config attribute is default
            return self.__default__(key)

        raise KeyError(
            f"{key!r} is not a valid attribute on the config {self.__classname__!r}"
        )

    def save(
        self,
        file: str | Path | TextIOWrapper | None = None,
        override: bool = False,
        defaults: bool = None,
    ):
        """Save the current configuration to a given save file. Accounts for
        provided save path in the decorator. If a nested config has a save path
        set in the decorator it will be saved to that file instead of the parents save path.
        If a save path is provided as an argument to this method then the override argument is
        automatically true. Overriding pulls in all nested configs recursively regardless of their
        save path and config type. This means all nested config options will be saved in a single
        file.

        Args:
            save_path (str | Path | TextIOWrapper): The path or file to where the config's json
                should written. Defaults to `None`.

            override (bool): If provided, all nested config classes are pulled into the same
                save/location. Otherwise, if a nested config class provides a save location
                then it will be saved there instead.

            defaults (bool): If provided the defaults for config values are also saved. By default
                default values are skipped.
        """
        if file is not None:
            override = True
        file = file or self.__tedconfig_save_path__

        if file is None:
            raise ValueError(
                "Must provide a save path or file in either the config decorator or in the \
save method arguments"
            )

        data = self.__build_save_dict__(override, defaults)
        if data != {}:
            self.__save__(data, file)

        return self

    @classmethod
    def defaults(cls: ConfigBase, file: str | Path | TextIOWrapper = None) -> dict:
        """`classmethod`: Return a dict representation of the configuration defaults.
        If a file is provided then the dict will be saved to that file.

        Returns:
            dict: dict representation of the configuration.
        """
        data = cls().__build_defaults_dict__() # pylint: disable=no-value-for-parameter

        if file is not None:
            cls.__save__(data, file)
        else:
            return data

    def __iter__(self):
        return iter(self.__tedconfig_attributes__.keys())

    def items(self):
        """Get a tuple iterator of key value pairs."""
        for key in self.__tedconfig_attributes__:
            yield key, getattr(self, key)

    def values(self):
        """Get an iterator of all attributes of the current config class."""
        for key in self.__tedconfig_attributes__:
            yield getattr(self, key)

    def keys(self):
        """Get an iterator of all attribute names of the current config class."""
        return iter(self.__tedconfig_attributes__.keys())

    def as_dict(self):
        """Convert the current config class into it's dict representation."""
        result = {}
        for key, value in self.__tedconfig_attributes__.items():
            if isinstance(getattr(self, key), ConfigBase):
                result[key] = getattr(self, key).as_dict()
            else:
                if key not in self.__tedconfig_validated__:
                    result[key] = self.__get_default__(value)
                else:
                    result[key] = getattr(self, key)
        return result

    def __getitem__(self, __name: str) -> Any:
        """Get a specific attribute from the config object."""
        if isinstance(__name, str) and hasattr(self, __name):
            return getattr(self, __name)
        raise IndexError(f"{__name} is not a valid attribute")

    def __setitem__(self, __name: str, value: Any) -> Any:
        """Set a specific value of the config. Must be valid."""
        if isinstance(__name, str) and hasattr(self, __name):
            self.__validate__(__name, value)
            setattr(self, __name, value)
        else:
            raise IndexError(f"{__name} is not a valid attribute")

    def __delitem__(self, __name: str) -> None:
        """Set the attribute to none. The attribute will still exist since it is part of the
        config.
        """
        if isinstance(__name, str) and hasattr(self, __name):
            setattr(self, __name, None)
        else:
            raise IndexError(f"{__name} is not a valid index")

    def __validate__(self, key: str, value: Any, parent: list[str] = None, context: dict = None) -> Any:
        parent = parent or [self.__classname__]
        context = context or self.__tedconfig_attributes__

        self.__vk_in_object__(key, parent, context)

        attr = context[key]
        if isinstance(attr, Options):
            self.__vk_options__(key, value, parent, context)
        elif isinstance(attr, (list, tuple)):
            self.__vk_collection__(key, value, parent, context)
        elif isinstance(attr, dict):
            self.__vk_dict__(key, value, parent, context)
        elif isinstance(attr, TypesDefault):
            self.__vk_types_default__(key, value, parent, context)
        else:
            self.__vk_generic__(key, value, parent, context)

    @staticmethod
    def __load__(file: str | Path | TextIOWrapper):
        """Load a config file, convert to a dictionary, and return the result."""

        with open(file, "r", encoding="utf-8") as json:
            return json_load(json)

    @staticmethod
    def __save__(data: dict, file: str | Path | TextIOWrapper):
        """Save the config as a dict to a specific file."""

        if isinstance(file, TextIOWrapper):
            _save_to_open_file(file, data)
        else:
            _save_to_file(file, data)

    def __parse__(self, cfg: Optional[dict] = None, parent: Optional[list[str]] = None):
        """Parse the values given a configuration in dict form. Sets the given value
        to the attribute on this class. Replaces the typing values with actual values."""

        if cfg is not None or self.__tedconfig_config__ is not None:
            # Evaluate data from provided dict
            cfg = cfg or self.__tedconfig_config__
        elif cfg is None and self.__tedconfig_load_path__ is not None:
            # Evaluate data after loading it from file
            cfg = self.__load__(self.__tedconfig_load_path__) 
        else:
            # Evaluate as empty config
            cfg = {}

        self.__tedconfig_config__ = cfg
        # Used for error tracing
        parent = parent or [self.__classname__]

        for key, value in cfg.items():
            self.__validate__(key, value, parent)

            attr = getattr(self, key)
            if _inherits_config_base(attr) and len(attr.__tedconfig_validated__) == 0:
                attr = attr.init()
                setattr(self, key, attr.__parse__(value, [*parent, attr.__classname__]))
                self.__tedconfig_validated__.append(key)
                continue

            self.__tedconfig_validated__.append(key)
            setattr(self, key, value)

        return self

    def __get_default__(self, value) -> Any:
        if isinstance(value, TypesDefault):
            return value.default

        if isinstance(value, Options):
            return value.default

        if isinstance(value, list):
            return list([val for val in value if not isinstance(val, type)])

        if isinstance(value, tuple):
            return tuple([val for val in value if not isinstance(val, type)])

        if isinstance(value, dict):
            new_value = {k: v for k,v in value.items() if k != "*"}
            for ikey, ivalue in new_value.items():
                new_value[ikey] = self.__get_default__(ivalue)
            return new_value

        if _inherits_config_base(_type(value)):
            return value.init()

        if isinstance(value, type):
            return value()

        if _inherits_config_base(value):
            return value.__parse__(parent=[self.__classname__])

        return value

    def __build_save_dict__(
        self, override: bool = False, save_defaults: bool = None
    ) -> Iterator[Any]:
        """Build the dict representation of the config's current state."""
        result = {}

        save_defaults = save_defaults or self.__tedconfig_save_defaults__

        for key, value in self.__tedconfig_attributes__.items():
            if key not in self.__tedconfig_validated__ and self.is_default(key):
                self.__tedconfig_validated__.append(key)
                value = self.__get_default__(value)
            else:
                value = getattr(self, key)

            if _inherits_config_base(value):
                if value.__tedconfig_save_path__ is not None and not override:
                    value.save()
                elif not value.is_default() or save_defaults:
                    result[key] = value.__build_save_dict__(override, save_defaults)
            elif not self.is_default(key) or save_defaults:
                result[key] = value
        
        return result

    def __build_defaults_dict__(self):
        """Build the default dict representation of the config class."""

        result = {}

        for key, value in self.__tedconfig_attributes__.items():
            if _inherits_config_base(value):
                result[key] = value.defaults()
            else:
                result[key] = self.__get_default__(value)
        return result

    def __default__(self, key):
        """Determine if a single attribute is it's default value."""

        attr = getattr(self, key)
        if isinstance(attr, TypesDefault) and attr.default == attr:
            return True

        if (
            isinstance(self.__tedconfig_attributes__[key], Options)
            and attr == self.__tedconfig_attributes__[key].default
        ):
            return True

        if isinstance(attr, type) and _inherits_config_base(attr):
            return True

        if (
            isinstance(self.__tedconfig_attributes__[key], type)
            and self.__tedconfig_attributes__[key]() == attr
        ):
            return True

        if _inherits_config_base(attr):
            return attr.is_default()

        if attr == self.__tedconfig_attributes__[key]:
            return True

        if self.__get_default__(self.__tedconfig_attributes__[key]) == attr:
            return True

        return False

    def __vk_in_object__(self, key, parent, context):
        if key not in context:
            raise ValueError(
                TED.parse(
                    f"Invalid variable [@F #eed49f]{key}[@F] in \
{_path([*parent, self.__classname__])}"
                )
            )

    def __vk_options__(self, key, value, parent, context: dict):
        attr = context[key]
        if not isinstance(value, attr.types):
            raise TypeError(
                TED.parse(
                    f"*{_path([*parent, self.__classname__, key])} must be \
on of these type(s): {', '.join(f'[@F #f5a97f]{val.__name__}[@]' for val in attr.types)}; \
was [@F 210]{_type(value).__name__}"
                )
            )

        if value not in attr.options:
            raise TypeError(
                TED.parse(
                    f"*{_path([*parent, self.__classname__, key])} must be one of the \
following values: \
({', '.join(p_value(val, decode=False) for val in attr.options)}); \
was {p_value(value, decode=False)}"
                )
            )
        self.__tedconfig_validated__.append(key)

    def __vk_collection__(self, key, value, parent, context):
        attr = context[key]
        if not isinstance(value, list):
            raise TypeError(
                TED.parse(
                    f"*{_path([*parent, self.__classname__, key])} must be a {_type(attr).__name__}\
 containing any of these types: \
{', '.join(f'[@F #f5a97f]{val.__name__}[@]' for val in _all_types(attr))}\
; was [@F 210]{type(value)}"
                )
            )

        if any(type(val) not in _all_types(attr) for val in value):
            invalids = list(
                filter(lambda val: type(val) not in _all_types(attr), value)
            )
            message = f"; contains invalid type(s) \
{', '.join([f'[@F 210]{type(i).__name__}[@]' for i in invalids])}"

            raise TypeError(
                TED.parse(
                    f"*{_path([*parent, self.__classname__, key])} must be a {_type(attr).__name__}\
 containing any of these type(s): \
{', '.join(f'[@F #f5a97f]{val.__name__}[@]' for val in _all_types(attr))}{message}"
                )
            )

    def __vk_dict__(self, key, value, parent, context: dict=None):
        attr = context[key]
        # Value must be a dict / same type as context[key]
        if not isinstance(value, _type(attr)):
            raise TypeError(
                TED.parse(
                    f"*{_path([*parent, self.__classname__, key])} must be a \
{_type(attr).__name__}; was [@F 210]{_type(attr).__name__}"
                )
            )

        # For each defined key in config check the type
        for ikey, ivalue in [(k, v) for k, v in value.items() if k in attr]:
            if not isinstance(ivalue, _type(attr.get(ikey))):
                raise TypeError(
                    TED.parse(
                        f"""*{
                            _path([*parent, self.__classname__, key, ikey])
} must be a {_type(attr.get(ikey)).__name__}; \
was [@F 210]{_type(value).__name__}"""
                    )
                )

        # Check wildcard on non defined keys
        if "*" in attr:
            for ikey in [k for k in value.keys() if k not in attr]:
                if "*" in attr:
                    self.__validate__("*", value[ikey], [*parent, key], context[key])

        # for each key in context[key] if that is also in value then recurse validate
        for ikey in [k for k in value.keys() if k in attr]:
            self.__validate__(ikey, value[ikey], [*parent, key], context[key])


    def __vk_generic__(self, key, value, parent, context):
        attr = _type(context[key])

        if (
            not _inherits_config_base(attr)
            and key not in self.__tedconfig_validated__
            and not isinstance(value, attr)
        ):
            raise TypeError(
                TED.parse(
                    f"*{_path([*parent, self.__classname__, key])} must be of type \
[@F #f5a97f]{attr.__name__}[@]; was [@F 210]{type(value).__name__}"
                )
            )

    def __vk_types_default__(self, key, value, parent, context):
        attr = context[key]
        if isinstance(attr, TypesDefault):
            if type(value) not in attr.types:
                raise TypeError(
                    TED.parse(
                        f"*{_path([*parent, self.__classname__, key])} must be one \
of these types ({', '.join(f'[@F #f5a97f]{_type(val).__name__}[@]' for val in attr.types)}); was \
[@F 210]{type(value).__name__}"
                    )
                )
            else:
                self.__tedconfig_validated__.append(key)

            if (
                isinstance(value, (list, tuple))
                and attr.nested_types is not None
                and any(type(val) not in attr.nested_types for val in value)
            ):
                raise ValueError(
                    TED.parse(
                        f"*Values in {_path([*parent, self.__classname__, key])} must be one \
of these types ({', '.join(f'[@F #f5a97f]{val.__name__}[@]' for val in attr.nested_types)})\
; was [@F 210]{type(value).__name__}"
                    )
                )
            else:
                self.__tedconfig_validated__.append(key)

    def pretty(self, depth: int = -1) -> str:
        """Encode with teddecor.pprint and return the formatted string.

        Args:
            depth (int): Depth of what to print. -1 means no limit otherwise dict, list, tuple
                objects are truncated with `{...}`, `[...]`, `(...)`, when the max depth is reached.
        """
        return p_value(self.as_dict(), depth=depth)

    def __str__(self) -> str:
        return str(self.as_dict())

    def __repr__(self) -> str:
        return f"Config<{self.__classname__}>"

    if TYPE_CHECKING:
        def __getattr__(self, attribute: str) -> Any: ...
        def __setattr__(self, attribute: str, value: object) -> None: ...
