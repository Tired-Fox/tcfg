from io import TextIOWrapper
from pathlib import Path
from typing import TYPE_CHECKING, Any

from .config_base import ConfigBase

def _process_config(
    cls: object=object,
    load: str | Path = None,
    save: str | Path = None,
    load_save: str | Path = None,
    save_defaults: bool = False,
    *,
    _type: str = "json",
):
    if load_save is not None:
        load = Path(load_save).resolve()
        save = Path(load_save).resolve()
    else:
        load = Path(load).resolve() if load is not None else None
        save = Path(save).resolve() if save is not None else None

    if _type == "yaml":
        from yaml import safe_load as yaml_load, safe_dump as yaml_dump

        class TEDyaml(ConfigBase, cls):
            def __init__(self, cfg=None):
                super().__init__(cls, cfg, save, load, save_defaults)

            def __call__(self, cfg=None):
                return TEDyaml(cfg)
            
            @staticmethod
            def __load__(file: str | Path | TextIOWrapper):
                if isinstance(file, (str, Path)):
                    with open(Path(file).resolve(), "r", encoding="utf-8") as load_file:
                        data = yaml_load(load_file)
                        return data
                else:
                    data = yaml_load(file)
                    return data

            @staticmethod
            def __save__(data: dict, file: str | Path | TextIOWrapper):
                if isinstance(file, (str, Path)):
                    with open(
                        Path(file).resolve(), "+w", encoding="utf-8"
                    ) as save_file:
                        yaml_dump(data, save_file, default_flow_style=False)
                else:
                    yaml_dump(data, file, default_flow_style=False)

        return TEDyaml
    elif _type == "toml":
        try:
            from tomllib import load as toml_load, dump as toml_dump
        except:
            try:
                from toml import load as toml_load, dump as toml_dump
            except:
                raise Exception(
                    "Either use python v3.11 for tomllib or install the python \
toml library."
                )

        class TEDtoml(ConfigBase):
            def __init__(self, cfg=None):
                super().__init__(cls, cfg, save, load, save_defaults)

            def __call__(self, cfg=None):
                return TEDyaml(cfg)

            @staticmethod
            def __load__(file: str | Path | TextIOWrapper):
                return toml_load(file)

            @staticmethod
            def __save__(data: dict, file: str | Path | TextIOWrapper):
                if isinstance(file, (str, Path)):
                    with open(
                        Path(file).resolve(), "+w", encoding="utf-8"
                    ) as save_file:
                        toml_dump(data, save_file)
                else:
                    toml_dump(data, file)
                
        return TEDtoml
    else:
        class TEDConfig(ConfigBase, cls):  # pylint: disable=missing-class-docstring
            # Base config class. Built from the attributes of another class.
            #   Similar to dataclass, but with typing and default values.

            def __init__(self, cfg=None):
                super().__init__(cls, cfg, save, load, save_defaults)

            def __call__(self, cfg=None):
                return TEDyaml(cfg)

        return TEDConfig


class config:
    """Construct a configuration class from the base classes attributes."""

    @classmethod
    def json(
        cls,
        wrap=None,
        *,
        load: str | Path | None = None,
        save: str | Path | None = None,
        load_save: str | Path | None = None,
        defaults: bool = False,
    ):
        """Construct a configuration class from the base classes attributes. Loads and saves
        with json files.
        """

        def wrapper(wrap=object):
            return _process_config(
                cls=wrap,
                load=load,
                save=save,
                load_save=load_save,
                save_defaults=defaults,
            )

        if wrap is None:
            return wrapper

        return wrapper(wrap)

    @classmethod
    def toml(
        cls,
        wrap=None,
        *,
        load: str | Path | None = None,
        save: str | Path | None = None,
        load_save: str | Path | None = None,
        defaults: bool = False,
    ):
        """Construct a configuration class from the base classes attributes. Loads and saves
        with toml files.
        """

        def wrapper(wrap=object):
            return _process_config(
                cls=wrap,
                load=load,
                save=save,
                load_save=load_save,
                save_defaults=defaults,
                _type="toml",
            )

        if wrap is None:
            return wrapper

        return wrapper(wrap)

    @classmethod
    def yaml(
        cls,
        wrap=None,
        *,
        load: str | Path | None = None,
        save: str | Path | None = None,
        load_save: str | Path | None = None,
        defaults: bool = False,
    ):
        """Construct a configuration class from the base classes attributes. Loads and saves
        with yaml files.
        """

        def wrapper(wrap=object):
            return _process_config(
                cls=wrap,
                load=load,
                save=save,
                load_save=load_save,
                save_defaults=defaults,
                _type="yaml",
            )

        if wrap is None:
            return wrapper

        return wrapper(wrap)

    def __init__(self, *args, **kwargs) -> None:
        raise Exception(
            "The base config class should not be instantiated. Use the classmethods\
to wrap other classes."
        )

    def __call__(self, *args, **kwargs):
        raise Exception(
            "The base config class should not be called. Use the classmethods\
to wrap other classes."
        )
