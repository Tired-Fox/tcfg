from tcfg import tcfg, Options, Path

@tcfg(path="nested.json")
class Nested:
    """Nested config"""

    port: int = 8081
    """Port number of the server."""

@tcfg(path="cfg.yml")
class Config:
    """Main config"""

    unique: tuple[int, Path, Options("Monday", "Friday")]
    """Unique id of the config."""

    nested: Nested
    """Nested server configurations."""

    extensions: list[str | dict[str, dict]]
    """List of extensions to use for the server."""

    path = Options("/home/", "/home/documents/")
    """Path to root of server. ONLY two paths supported."""

    random: Path
    """Random path. Is normalized and has `/` stripped from ends. Stored as a string."""

print(dict(Config()))
config = Config()
print(config.nested.port)
