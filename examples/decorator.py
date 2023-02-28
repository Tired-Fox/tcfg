from tcfg import Path, tcfg
from typing import Literal


@tcfg
class SuperNested:
    extra: str


@tcfg(path="nested.json")
class Nested:
    """Nested config"""

    port: int = 8081
    """Port number of the server."""

    sup_nest: SuperNested


@tcfg(path="cfg.yml")
class Config:
    """Main config"""

    unique: str
    """Unique id of the config."""

    nested: Nested
    """Nested server configurations."""

    deep: SuperNested

    extensions: list[str | dict[str, dict]]
    """List of extensions to use for the server."""

    path: Literal['/home/', '/home/documents']
    """Path to root of server. ONLY two paths supported."""

    random: str = Path('/random/dir')
    """Random path. Is normalized and has `/` stripped from ends. Stored as a
    string."""


print(dict(Config()))
config = Config()
print(config.nested.port)
