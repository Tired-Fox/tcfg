from .cfg import cfg
from .reserved import *

def tcfg(
    cls=None,
    *,
    path: str = None,
) -> cfg:
    """Decorator to convert a class to a configuration class object."""

    def wrapper(wrap=object) -> cfg:
        if path is not None:
            class Config(cfg, wrap):
                """Config class from the config base class and the wrapped class."""
                _path_ = path
            return Config
        else:
            class Config(cfg, wrap):
                """Config class from the config base class and the wrapped class."""
            return Config

    if cls is None:
        return wrapper

    return wrapper(cls)
