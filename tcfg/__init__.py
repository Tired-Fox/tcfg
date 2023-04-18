from .config import cfg
from .type_check import type_check, PathType, ConfigTypeError, Option, new

__all__ = [
    "type_check",
    "cfg",
    "PathType",
    "ConfigTypeError"
]

__version__ = "0.4.5"
