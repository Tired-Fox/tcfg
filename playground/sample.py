from tcfg import cfg

@cfg.json
class Markdown:
    enabled = False

@cfg.json(load="cfg.json")
class Config:
    """Test Configuration"""
    data = ""

    markdown = Markdown

print(Config().as_dict())
