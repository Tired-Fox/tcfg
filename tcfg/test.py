from dataclasses import dataclass
from teddecor.decorators import config, Options

@dataclass
class Days:
    Monday: str = "Monday"
    Tuesday: str = "Tuesday"
    Wednesday: str = "Wednesday"
    Thursday: str = "Thursday"
    Friday: str = "Friday"

@config.toml
class Config:
    sample = {
        "*": str,
        "class": [str],
        "extensions": dict,
        "is_flag": bool,
    }
    day = Options(Days, default=Days.Friday)

cfg = Config({
    
})

print(cfg.__build_save_dict__(False, False))