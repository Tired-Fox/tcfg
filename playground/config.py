from tcfg import cfg, Option, PathType, new

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

def fake_server_start(config: Config):
    url = f"http://{config.server.host}:{config.server.port}/{config.root}"
    if config.server.open:
        print("Opening local server at:", url)
    else:
        print("Server started at:", url)

    print("Watching paths:")
    for path in config.server.watch:
        print(f" - {path!r}")

    print("Ignoring any path with:", config.ignore)

if __name__ == "__main__":
    config = Config()
    fake_server_start(config)

