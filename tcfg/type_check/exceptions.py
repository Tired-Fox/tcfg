from .base import Type, UnionAlias, type_str, LiteralGenericAlias


ERROR = "\x1b[4;31m{}\x1b[39;24m"

def _format_(value) -> str:
    if isinstance(value, str):
        return repr(value)
    return type_str(value)

def _format_type_pairs_(_type: Type) -> tuple[str, str, str, str]:
    if isinstance(_type, UnionAlias):
        return ("", "", "", " | ")
    elif isinstance(_type, type):
        return ("", "", "", "")
    else:
        return (f"{_type.__name__}","[", "]", ", ")

def _format_full_(_type: Type) -> str:
    if isinstance(_type, UnionAlias):
        return ERROR.format(' | '.join(type_str(arg) for arg in _type.__args__))
    elif isinstance(_type, type):
        return ERROR.format(type_str(_type))
    else:
        if isinstance(_type, LiteralGenericAlias):
            args = ', '.join(repr(arg) for arg in _type.__args__)
        else:
            args = ', '.join(type_str(arg) for arg in _type.__args__)
        return f"{ERROR.format(_type.__name__)}[{args}]"

                          
def _type_error_(_parents_: list[tuple[Type, int | None]]):
    message = ""
    if len(_parents_) > 0:
        problem, idx = _parents_.pop()
        if idx is None:
            message = _format_full_(problem)
        else:
            pairs = _format_type_pairs_(problem)
            message = (
                pairs[0] + pairs[1]
                + pairs[3].join(
                    _format_(t) if i != idx else ERROR.format(_format_(t))
                    for i, t in enumerate(problem.__args__)
                )
                + pairs[2]
            )

        _parents_.reverse()
        for parent, idx in _parents_:
            pairs = _format_type_pairs_(parent)
            args = pairs[3].join(
                _format_(t) if i != idx else message for i, t in enumerate(parent.__args__)
            )
            message = f"{pairs[0]}{pairs[1]}{args}{pairs[2]}"

    return message


class ConfigTypeError(Exception):
    __module__ = Exception.__module__
    def __init__(self, parents: list, message: str):
        self.parents = parents
        self.message = message

    def __str__(self):
        return f"\x1b[1m{_type_error_(self.parents)}\x1b[22m\n  {self.message}"

class CustomTypeError(Exception):
    __module__ = Exception.__module__
    def __init__(self, message: str, *, arg: str|None = None):
        self.arg = arg
        self.message = message

    def __str__(self):
        return self.message

