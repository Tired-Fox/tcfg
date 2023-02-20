from tcfg import cfg, Path, Options

class Nested(cfg):
    """Nested config"""

    _path_ = "nested.json"

    port: int = 8081
    """Port number of the server."""

class Config(cfg):
    """Main config"""

    _path_ = "cfg.yml"

    unique: str
    """Unique id of the config."""

    nested: Nested
    """Nested server configurations."""

    extensions: list[str | dict[str, dict]]
    """List of extensions to use for the server."""

    path: str = Options("/home/", "/home/documents/")

    random: Path

if __name__ == "__main__":
    config = Config()
    print(config.as_dict())
    print(config.nested.port)
