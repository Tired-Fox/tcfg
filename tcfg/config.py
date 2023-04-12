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

import pathlib
import re

from types import GenericAlias, UnionType
from typing import TypeAlias, get_type_hints, Any, Literal

from json import loads as json_load, dumps as json_dump
from pyparsing import Iterator
from toml import loads as toml_load, dumps as toml_dump
from yaml import safe_load as yml_load, dump as yml_dump

from .reserved import TypePath, MISSING

from saimll import ppath, SAIML, p_value

LiteralGenericAlias: TypeAlias = type(Literal[''])


def ptype(_type: str, quotes: bool = True) -> str:
    markup = SAIML.parse(f"[@F #f5a97f $]{_type}[@F]")

    if quotes:
        return f"'{markup}'"
    return markup


def new_type(
    _type: UnionType | type | GenericAlias | LiteralGenericAlias,
    parents: list[str]
) -> CFGGenericAlias | CFGUnionType | CFGType | CFGLiteral:
    """Generate a config validation type from a new_type."""

    if isinstance(_type, UnionType):
        return CFGUnionType(_type, parents)
    if isinstance(_type, GenericAlias):
        return CFGGenericAlias.new(_type, parents)
    if isinstance(_type, LiteralGenericAlias):
        return CFGLiteral(_type, parents)
    if isinstance(_type, type):
        return CFGType(_type, parents)

    raise Exception(f"{ppath(*parents, spr='.')}; Unkown type hint {_type}")


def get_type(value: Any) -> type:
    """Get the type of the value. If it is already a type then the value is
    returned.
    """
    if isinstance(value, type):
        return value
    return type(value)


def parse_type(_type: type | Any, parents: list[str]) -> type:
    """Parse and return a TCFG type that can be validated."""

    if isinstance(_type, (GenericAlias, UnionType)):
        _type = new_type(_type, [*parents, "type_hint"])
        return _type

    return new_type(_type, [*parents, "type_hint"])


def setup_default(default: Any):
    """Create copies of dict, list, tuple, and set. Return passed value
    otherwise.
    """
    if isinstance(default, (dict, list, tuple, set)):
        return type(default)(default)
    return default


def parse_valid_value(
        _type: CFGType | CFGUnionType | CFGGenericAlias | type,
        value: Any
):
    """Parse the config value, if it is one of the special config types then
    return the transformed value.
    """
    if isinstance(_type, CFGType) and _type.type == TypePath or _type == TypePath:
        return TypePath.normalize(value)
    return value


def is_reserved(_type):
    return _type in [TypePath]


def validate_reserved(value, _type, parents):
    if _type == TypePath:
        if not isinstance(value, str):
            raise TypeError(
                f"{ppath(*parents, spr='.')}; invalid type \
{ptype(type(value).__name__)}, expected {ptype('str')}"
            )
        return TypePath.normalize(value)


valid_type = (int, float, bool, str, list, dict, TypePath)


class CFGGenericAlias:
    """Base type that can validate a value."""

    @staticmethod
    def new(_type: GenericAlias, parents: list[str]) -> CFGGenericAlias:
        """Create a specific generic alias config validation type from a
        GenericAlias type hint.
        """

        name = re.match(
            r"(?:typing.*)?(?P<name>set|dict|list|tuple)\[.+\]",
            str(_type),
            re.IGNORECASE
        )

        if name is not None:
            name = name.group("name")
        else:
            raise TypeError(
                f"{ppath(*parents, spr='.')}; Unkown GenericAlias name for \
{_type!r}")

        if name == "set":
            return CFGGenericAlias.CFGSetType(_type.__args__, parents)
        if name == "list":
            return CFGGenericAlias.CFGListType(_type.__args__, parents)
        if name == "tuple":
            return CFGGenericAlias.CFGTupleType(_type.__args__, parents)
        if name == "dict":
            return CFGGenericAlias.CFGDictType(_type.__args__, parents)

        raise TypeError(
            f"{ppath(*parents, spr='.')}; Unkown GenericAlias name for \
{_type!r}")

    class CFGDictType:
        """Dict type that can validate a value."""

        def __init__(
            self,
            types: set(type | GenericAlias | UnionType),
            parents: list[str]
        ) -> None:
            self.name = "dict"

            value_types = list(types)
            if len(value_types) > 2:
                raise TypeError(
                    f"{ppath(*parents, spr='.')}; Dict type must only have \
two listed types. One for the key and one for the value."
                )

            if (
                len(value_types) >= 1
                and isinstance(value_types[0], type)
                and value_types[0] != str
            ):
                raise TypeError(
                    f"{ppath(*parents, spr='.')}; Configuration dict keys \
must always be of type {ptype('str')} \
<dict[{SAIML.parse(f'[@Fred$]{value_types[0].__name__}')}, \
{new_type(value_types[1], [*parents, 'dict_value'])}]>"
                )

            self.value_type = new_type(
                value_types[1], [*parents, "dict_value"])

        def default(self) -> dict:
            """Default value of the configuration type."""
            return dict()

        def validate(self, value: dict, parents: list[str]):
            """Validate a value according to this objects typing."""
            if not isinstance(value, dict):
                raise TypeError(
                    f"{ppath(*parents, spr='.')}; invalid type \
{ptype(type(value).__name__)}, expected {ptype('dict')}"
                )

            for key, item in value.items():
                try:
                    value[key] = self.value_type.validate(item, parents)
                except TypeError as exc:
                    raise TypeError(
                        f"{ppath(*parents, spr='.')}; invalid dict value type \
{ptype(type(item).__name__)}, expected {self.value_type!r}"
                    ) from exc

            return dict(value)

        def __repr__(self) -> str:
            return f"'{self}'"

        def __str__(self) -> str:
            return f"dict[str, {self.value_type}]"

    class CFGTupleType:
        """Tuple type that can validate a value."""

        def __init__(
            self,
            item_types: set[type | UnionType | GenericAlias],
            parents: list[str]
        ) -> None:
            self.name = "tuple"
            self.item_types = [new_type(it, [*parents, "tuple"])
                               for it in list(item_types)]

        def default(self) -> tuple:
            """Default value of the configuration type."""
            return tuple()

        def validate(self, value: Any, parents: list[str]) -> tuple:
            """Validate a value according to this objects typing."""
            if not isinstance(value, list):
                raise TypeError(
                    f"{ppath(*parents, spr='.')}; invalid value type \
{ptype(type(value).__name__)}, expected {ptype('list')}"
                )

            if len(self.item_types) != len(value):
                amount = "Too many" if len(value) > len(
                    self.item_types) else "Too few"
                plural = ("were", "s") if len(value) > 1 else ("was", "")
                raise TypeError(
                    f"{ppath(*parents, spr='.')}; {amount} items in value, \
expected {ptype(len(self.item_types), False)} items but there {plural[0]} \
{ptype(len(value), False)} item{plural[1]}"
                )

            value = list(value)
            for i, (item, _type) in enumerate(zip(value, self.item_types)):
                try:
                    value[i] = _type.validate(item, parents)
                except TypeError as exc:
                    raise TypeError(
                        f"{ppath(*parents, spr='.')}; invalid item type \
{ptype(type(item).__name__)} at index {i}, expected {ptype(_type)}"
                    ) from exc

            return tuple(value)

        def __repr__(self) -> str:
            return str(self)

        def __str__(self) -> str:
            return f"tuple[{', '.join(str(it) for it in self.item_types)}]"

    class CFGListType:
        """List type that can validate a value."""

        def __init__(
            self,
            item_types: set(type | GenericAlias | UnionType),
            parents: list[str]
        ) -> None:
            self.name = "list"
            self.item_type = new_type(item_types[0], [*parents, "list"])

        def default(self) -> list:
            """Default value of the configuration type."""
            return list()

        def validate(self, value: Any, parents: list[str]) -> bool:
            """Validate a value according to this objects typing."""
            if not isinstance(value, list):
                raise TypeError(
                    f"{ppath(*parents, spr='.')}; invalid value type \
{ptype(type(value).__name__)} expected {ptype('list')}"
                )

            for i, item in enumerate(value):
                try:
                    value[i] = self.item_type.validate(item, parents)
                except TypeError as exc:
                    raise TypeError(
                        f"{ppath(*parents, spr='.')}; invalid item type \
{ptype(type(item).__name__)} at index {ptype(i, False)}, expected \
{ptype(self.item_type)}"
                    ) from exc

            return value

        def __repr__(self) -> str:
            return str(self)

        def __str__(self) -> str:
            return f"list[{self.item_type}]"

    class CFGSetType:
        """Set type that can validate a value."""

        def __init__(
            self,
            item_types: set(type | GenericAlias | UnionType),
            parents: list[str]
        ) -> None:
            self.name = "set"
            self.item_type = new_type(item_types[0], [*parents, "set"])

        def default(self) -> set:
            """Default value of the configuration type."""
            return set()

        def validate(self, value: Any, parents: list[str]) -> bool:
            """Validate a value according to this objects typing."""
            if not isinstance(value, list):
                raise TypeError(
                    f"{ppath(*parents, spr='.')}; invalid value type \
{ptype(type(value).__name__)} expected {ptype('list')}"
                )

            value = list(value)
            for i, item in enumerate(value):
                try:
                    value[i] = self.item_type.validate(item, parents)
                except TypeError as exc:
                    raise TypeError(
                        f"{ppath(*parents, spr='.')}; invalid item type \
{ptype(type(item).__name__)} at index {ptype(i, False)}, expected \
{ptype(str(self.item_type))}"
                    ) from exc

            return set(value)

        def __repr__(self) -> str:
            return str(self)

        def __str__(self) -> str:
            return f"set[{self.item_type}]"


class CFGUnionType:
    """Union type that can validate a value."""

    def __init__(self, _type: UnionType, parents: list[str]) -> None:
        self.types = [new_type(it, [*parents, "union"])
                      for it in list(_type.__args__)]
        self.parents = parents

    def default(self) -> Any:
        """Default value of the configuration type."""
        return self.types[0]()

    def validate(self, value: Any, parents: list[str]):
        """Validate the value to be one of the unions types."""

        for _type in self.types:
            try:
                return _type.validate(value, [*parents, "union", "_type"])
            except TypeError:
                pass
        raise TypeError(
            f"{ppath(*parents, spr='.')}; invalid type \
{ptype(type(value).__name__)}, expected one of \
{', '.join(ptype(str(v)) for v in self.types)}"
        )

    def __repr__(self) -> str:
        return f"'{self}'"

    def __str__(self) -> str:
        return " | ".join(str(it) for it in self.types)


class CFGLiteral:
    """Represents a literal option for the configuration type.
    Coniguration value must match one of the literal values in this literal
    type.
    """

    def __init__(self, literal: LiteralGenericAlias, parents: list[str]):
        self.literals = literal.__args__

    def default(self) -> Any:
        """Default value of the literal type. Will
        be the first value of the typing.Literal type.
        """
        return self.literals[0]

    def validate(self, value: Any, parents: list[str]) -> bool:
        """Validate that a given value is one of the literal values.
        """

        for option in self.literals:
            if is_reserved(get_type(option)):
                return validate_reserved(value, TypePath, parents)
            if value == option:
                return value

        raise TypeError(f"{ppath(*parents, spr='.')}; invalid value \
{p_value(value)}, expected one of: \
{p_value(self.literals)}")

    def __repr__(self):
        return f'{self}'

    def __str__(self) -> str:
        options = [f'"{option}"' for option in self.literals]
        return f'Literal[{", ".join(options)}]'


class CFGType:
    """Type that can be validated."""

    def __init__(self, _type: type, parents: list[str]) -> None:
        if (
            cfg not in _type.__bases__
            and _type not in valid_type
        ):
            raise TypeError(f"{ppath(*parents, spr='.')}; invalid type \
{ptype(_type.__name__)}, expected one of: \
{ppath(*[v.__name__ for v in valid_type],spr=', ')}")

        self.type = _type

    def default(self) -> tuple:
        """Default value of the configuration type."""
        return self.type()

    def validate(self, value: Any, parents: list[str]):
        """Validate a value is and instance this type."""

        if is_reserved(self.type):
            return validate_reserved(value, self.type, parents)
        elif not isinstance(value, self.type):
            raise TypeError(
                f"{ppath(*parents, spr='.')}; invalid type \
{ptype(type(value).__name__)}, \
expected {ptype(self.type.__name__)}"
            )

        return parse_valid_value(self.type, value)

    def __repr__(self) -> str:
        return f"'{self}'"

    def __str__(self) -> str:
        return get_type(self.type).__name__

# ? CONFIG LOGIC


class cfg:
    """Base typed config class."""

    _path_: str = ""
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
        data: dict = None,
        parents: list[str] = None,
        *,
        strict: bool = True,
        skip_invalid: bool = False
    ) -> None:

        if parents is None:
            parents = [self.__class__.__name__]

        cfg.__tcfg_setup__(self, parents)
        self.__tcfg_strict__ = strict
        self.__tcfg_skip_invalid__ = skip_invalid

        if self._path_ != MISSING:
            # open and parse the config file
            file_path = pathlib.Path(self._path_.strip("/"))
            if not file_path.is_file():
                data = data or {}
            else:
                extension = file_path.suffix.lstrip(".")
                with open(file_path, "r", encoding="utf-8") as cfg_file:
                    if not hasattr(self, f"load_{extension}"):
                        raise LookupError(
                            f"Load callback for config extensions of \
'.{extension}' not found; must have load_{extension} defined to load \
'.{extension}' files")

                    if not ismethod(getattr(self, f"load_{extension}")):
                        raise TypeError(f"load_{extension} must be a method")

                    text = cfg_file.read()
                    data = getattr(self, f"load_{extension}")(text) or {}
        else:
            data = data or {}

        self.__validate__(data, parents)

    def __tcfg_setup__(self, parents: list[str]):
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
                __tcfg_values__[i[0]] = {
                    "type": MISSING, "default": setup_default(i[1])}

        # Get annotations for class attributes
        for anno, _type in get_type_hints(type(self)).items():
            if not anno.startswith("_"):
                if anno not in __tcfg_values__:
                    __tcfg_values__[anno] = {
                        "type": MISSING, "default": MISSING}

                __tcfg_values__[anno]["type"] = parse_type(
                    _type, [*parents, anno])

        # Create annotations and default values for class attributes
        # They are only created if they are MISSING
        for attr, data in __tcfg_values__.items():
            if data["type"] == MISSING:
                data["type"] = parse_type(
                    get_type(data["default"]), [*parents, attr])

            if data["default"] == MISSING:
                if (
                    not isinstance(data["type"], CFGType)
                    or cfg not in data["type"].type.__bases__
                ):
                    data["default"] = data["type"].default()

            if isinstance(data["default"], TypePath):
                data["type"] = parse_type(TypePath, [*parents, attr])
                data["default"] = str(data["default"])

            setattr(self, attr, data["default"])

        setattr(self, "__tcfg_values__", __tcfg_values__)

    def __tcfg_attributes__(self):
        """Parse and normalize tcfg class attributes for a given object."""

        # Normalize the seperators in the _path_ and strip `/` from the ends
        _path_ = TypePath.normalize(getattr(self, "_path_") or "")
        setattr(self, "_path_", _path_ if _path_ != "" else MISSING)

    def __validate__(self, data: dict, parents: list[str] = None):
        """Validate the values from the configuration dict and set the values
        accordingly.
        """

        if not isinstance(data, dict):
            raise TypeError(
                f"Can not validate configuration of type {type(data)}")

        for key, value in data.items():
            if key not in self.__tcfg_values__ and self.__tcfg_strict__:
                raise KeyError(
                    f"{ppath(*parents, spr='.')}; invalid configuration key \
{key!r}")

            if not (
                isinstance(self.__tcfg_values__[key]["type"], CFGType)
                and cfg in self.__tcfg_values__[key]["type"].type.__bases__
            ):
                value = self.__tcfg_values__[
                    key]["type"].validate(value, [*parents, key])
                setattr(self, key, value)

        for key, value in self.__tcfg_values__.items():
            if (
                isinstance(self.__tcfg_values__[key]["type"], CFGType)
                and cfg in self.__tcfg_values__[key]["type"].type.__bases__
            ):
                data_value = data[key] if key in data else {}
                setattr(
                    self,
                    key,
                    self.__tcfg_values__[key]["type"].type(
                        data_value, [*parents, key])
                )

    def __iter__(self) -> Iterator[str, Any]:
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
                    cfg_value.save(defaults)
                except Exception:
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
        file_path = pathlib.Path(self._path_)

        extension = file_path.suffix.lstrip(".")
        with open(file_path, "+w", encoding="utf-8") as cfg_file:
            if not hasattr(self, f"save_{extension}"):
                raise LookupError(
                    f"Save callback for config extensions of '.{extension}' \
not found; must have save_{extension} defined to save '.{extension}' files")

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
