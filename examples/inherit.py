from tcfg import Path, config
from typing import Literal


class Nested(config):
    """Nested config"""

    _path_ = "nested.json"

    port: int = 8081
    """Port number of the server."""


class Config(config):
    """Main config"""

    _path_ = "cfg.yml"

    unique: str
    """Unique id of the config."""

    nested: Nested
    """Nested server configurations."""

    extensions: list[str | dict[str, dict]]
    """List of extensions to use for the server."""

    path: Literal['/home/', '/home/documents']

    random: Path


if __name__ == "__main__":
    config = Config()
    print(config.as_dict())
    print(config.nested.port)
