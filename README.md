# tcfg

```python
from tcfg import cfg, Option

@cfg.json('cfg.json')
class Config:
  # year must be a string. It has a default value of '2023'
  year = '2023' 
  
  # load must be a boolean. It has a default value of true
  load = true 
  
@cfg.toml('cfg.toml')
class Config2:
  # year must be a string. Default to ''
  year = str
  
  # load must be a boolean. Default to false
  load = bool 
 
# Any config class will save to the specified file path unless overridden.
# This includes config classes that are in other config classes.
# This means you can have one master config object in your code that uses many config files.
@cfg.yaml('nested.tml')
class Nested:
  # Must be a bool. Defaults to false
  enabled = false
  
  # Must be an int. Defaults to 8081
  port = 8081 
  
  # Can specify multiple specific options.
  scope = Option('public', 'private', default='private') 
  
  # Must be a list
  # Literals are defaults and types are used for valid element types. Literal types are also used in element types.
  extensions = ['reload', dict]
  
  options = {
    # wildcard type used for validation of extra values not specified as a key in this dict
    '*': dict, 
    'open': false,
    # can have recursive nesting
    'deep_nesting': {
      'random': int 
    }
  }
 
@cfg.yaml('cfg.yml')
class Config3:
  nested = Nested # nested is a sub/nested config section
```
