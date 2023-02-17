"""teddecor.decorators.config

Allows  user to define classes representing configuration sections. It can automatically load
from a provided load path, and save to a provided save path. Allows for strict typing of
configuration values and for default values. Currently JSON, TOML, and YAML are supported.

With the configurations being setup in classes you may use dot notation to access the variables.

Example:
    If you have a json file that looks like this

    ```json
    {
        "extensions": ["sample", "example"],
        "validate": true
    }
    ```

    and setup the configuration class like this

    ```python
    @config.json(load="file_path.json")
    class Config:
        extensions = [str]
        validate = False

    cfg = Config.init()
    ```

    you can access the validate variable with

    ```python
    cfg.validate
    ```
"""

from .config import config as cfg
from .config_base import ConfigBase
from .types_default import TypesDefault, Options
