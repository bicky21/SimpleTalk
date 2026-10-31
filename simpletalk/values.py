"""How SimpleTalk values behave: showing them, comparing them, naming their type.

SimpleTalk has six kinds of value:
    number   42, 3.5
    text     "hello"
    bool     true, false
    list     [1, 2, 3]
    none     none
    fn       something made with `fn`, or a built-in like len()
"""

import math


class Function:
    def __init__(self, name, params, body, closure):
        self.name = name
        self.params = params
        self.body = body
        self.closure = closure

    def __repr__(self):
        return f"<fn {self.name}>"


class Builtin:
    def __init__(self, name, fn, min_args, max_args, usage):
        self.name = name
        self.fn = fn
        self.min_args = min_args
        self.max_args = max_args   # None = any number
        self.usage = usage

    def __repr__(self):
        return f"<built-in fn {self.name}>"


def is_number(v):
    return isinstance(v, (int, float)) and not isinstance(v, bool)


def tidy_number(n):
    """Turn 2.0 into 2 so results look the way people expect."""
    if isinstance(n, float) and math.isfinite(n) and n.is_integer() and abs(n) < 1e15:
        return int(n)
    return n


def type_name(v):
    if v is None:
        return "none"
    if isinstance(v, bool):
        return "bool"
    if is_number(v):
        return "number"
    if isinstance(v, str):
        return "text"
    if isinstance(v, list):
        return "list"
    if isinstance(v, (Function, Builtin)):
        return "fn"
    return "unknown"


def show(v, nested=False):
    """Turn any value into the text that `out` prints."""
    if v is None:
        return "none"
    if v is True:
        return "true"
    if v is False:
        return "false"
    if isinstance(v, int):
        return str(v)
    if isinstance(v, float):
        if math.isnan(v):
            return "not a number"
        if math.isinf(v):
            return "infinity" if v > 0 else "-infinity"
        v = tidy_number(round(v, 10))
        if isinstance(v, int):
            return str(v)
        return repr(v)
    if isinstance(v, str):
        return '"' + v + '"' if nested else v
    if isinstance(v, list):
        return "[" + ", ".join(show(x, nested=True) for x in v) + "]"
    if isinstance(v, (Function, Builtin)):
        return repr(v)
    return str(v)


def equal(a, b):
    """Strict but friendly equality: 1 = 1.0, but 1 is not "1" and not true."""
    if is_number(a) and is_number(b):
        return a == b
    if type(a) is bool or type(b) is bool:
        return a is b
    if isinstance(a, list) and isinstance(b, list):
        return len(a) == len(b) and all(equal(x, y) for x, y in zip(a, b))
    if type_name(a) != type_name(b):
        return False
    return a == b
