"""Built-in functions every SimpleTalk program can use.

Keep this list small and stable: adding is fine, renaming or removing breaks
people's programs.
"""

import math
import random as _random
import time

from .errors import RuntimeProblem
from .values import Builtin, is_number, show, tidy_number, type_name


def problem(message, hint=None):
    return RuntimeProblem(message, hint=hint)


def need_number(fn, v, what="a number"):
    if not is_number(v):
        raise problem(f"{fn}() needs {what}, but got {type_name(v)} {show(v, True)}.")
    return v


def need_whole(fn, v, what="a whole number"):
    need_number(fn, v, what)
    if isinstance(v, float):
        if not v.is_integer():
            raise problem(f"{fn}() needs {what}, but got {show(v)}.")
        v = int(v)
    return v


def need_text(fn, v):
    if not isinstance(v, str):
        raise problem(f"{fn}() needs text, but got {type_name(v)} {show(v, True)}.",
                      hint="Turn it into text first with txt(...).")
    return v


def need_list(fn, v):
    if not isinstance(v, list):
        raise problem(f"{fn}() needs a list, but got {type_name(v)} {show(v, True)}.")
    return v


# ------------------------------------------------------------------ the functions
def b_length(x):
    if isinstance(x, (str, list)):
        return len(x)
    raise problem(f"len() works on text or lists, not on {type_name(x)}.")


def b_number(x):
    if is_number(x):
        return x
    if isinstance(x, str):
        s = x.strip().replace("_", "")
        try:
            return int(s)
        except ValueError:
            pass
        try:
            f = float(s)
            if math.isfinite(f):
                return tidy_number(f)
        except ValueError:
            pass
        raise problem(f'"{x}" doesn\'t look like a number.',
                      hint="Check first with isnum(...).")
    raise problem(f"I can't turn {type_name(x)} into a number.")


def b_is_number(x):
    if is_number(x):
        return True
    if isinstance(x, str):
        try:
            b_number(x)
            return True
        except RuntimeProblem:
            return False
    return False


def b_text(x):
    return show(x)


def b_round(x, digits=0):
    need_number("round", x)
    digits = need_whole("round", digits, "a whole number of digits")
    # Round half away from zero (2.5 -> 3), which is what people expect at school.
    factor = 10 ** digits
    value = math.floor(abs(x) * factor + 0.5) / factor
    return tidy_number(math.copysign(value, x) if value else 0)


def b_abs(x):
    return abs(need_number("abs", x))


def b_sqrt(x):
    need_number("sqrt", x)
    if x < 0:
        raise problem("sqrt() can't take the square root of a negative number.")
    return tidy_number(math.sqrt(x))


def b_power(x, y):
    need_number("pow", x)
    need_number("pow", y)
    try:
        return tidy_number(x ** y)
    except (OverflowError, ZeroDivisionError):
        raise problem("pow() result is too big or not defined.")


def b_random(low, high):
    low = need_whole("rand", low)
    high = need_whole("rand", high)
    if low > high:
        low, high = high, low
    return _random.randint(low, high)


def _many_numbers(fn, args):
    items = args[0] if len(args) == 1 and isinstance(args[0], list) else list(args)
    if not items:
        raise problem(f"{fn}() needs at least one number.")
    for v in items:
        need_number(fn, v)
    return items


def b_min(*args):
    return min(_many_numbers("min", args))


def b_max(*args):
    return max(_many_numbers("max", args))


def b_sum(items):
    need_list("sum", items)
    for v in items:
        need_number("sum", v, "a list of numbers")
    return tidy_number(sum(items))


def b_upper(t):
    return need_text("upper", t).upper()


def b_lower(t):
    return need_text("lower", t).lower()


def b_trim(t):
    return need_text("trim", t).strip()


def b_replace(t, old, new):
    need_text("swap", t)
    need_text("swap", old)
    need_text("swap", new)
    return t.replace(old, new)


def b_split(t, sep=None):
    need_text("split", t)
    if sep is None:
        return t.split()
    need_text("split", sep)
    if sep == "":
        return list(t)
    return t.split(sep)


def b_join(items, sep=""):
    need_list("join", items)
    need_text("join", sep)
    return sep.join(show(v) for v in items)


def b_sort(items):
    need_list("sort", items)
    if all(is_number(v) for v in items) or all(isinstance(v, str) for v in items):
        return sorted(items)
    raise problem("sort() needs a list of only numbers or only text.")


def b_reverse(x):
    if isinstance(x, list):
        return list(reversed(x))
    if isinstance(x, str):
        return x[::-1]
    raise problem(f"rev() works on text or lists, not on {type_name(x)}.")


def b_copy(items):
    need_list("copy", items)
    return list(items)


def b_type(x):
    return type_name(x)


def b_wait(seconds):
    need_number("wait", seconds)
    if seconds < 0:
        raise problem("wait() can't wait a negative amount of time.")
    time.sleep(seconds)
    return None


BUILTINS = {}


def _register(name, fn, min_args, max_args, usage):
    BUILTINS[name] = Builtin(name, fn, min_args, max_args, usage)


_register("len", b_length, 1, 1, 'len("hello") -> 5')
_register("num", b_number, 1, 1, 'num("42") -> 42')
_register("isnum", b_is_number, 1, 1, 'isnum("42") -> true')
_register("txt", b_text, 1, 1, 'txt(42) -> "42"')
_register("type", b_type, 1, 1, 'type(42) -> "number"')
_register("round", b_round, 1, 2, "round(3.14159, 2) -> 3.14")
_register("abs", b_abs, 1, 1, "abs(-5) -> 5")
_register("sqrt", b_sqrt, 1, 1, "sqrt(16) -> 4")
_register("pow", b_power, 2, 2, "pow(2, 10) -> 1024")
_register("rand", b_random, 2, 2, "rand(1, 6) -> a dice roll")
_register("min", b_min, 1, None, "min(3, 1, 2) -> 1")
_register("max", b_max, 1, None, "max([3, 1, 2]) -> 3")
_register("sum", b_sum, 1, 1, "sum([1, 2, 3]) -> 6")
_register("upper", b_upper, 1, 1, 'upper("hi") -> "HI"')
_register("lower", b_lower, 1, 1, 'lower("HI") -> "hi"')
_register("trim", b_trim, 1, 1, 'trim("  hi  ") -> "hi"')
_register("swap", b_replace, 3, 3, 'swap("cat", "c", "b") -> "bat"')
_register("split", b_split, 1, 2, 'split("a,b", ",") -> ["a", "b"]')
_register("join", b_join, 1, 2, 'join(["a", "b"], "-") -> "a-b"')
_register("sort", b_sort, 1, 1, "sort([3, 1, 2]) -> [1, 2, 3]")
_register("rev", b_reverse, 1, 1, "rev([1, 2, 3]) -> [3, 2, 1]")
_register("copy", b_copy, 1, 1, "copy(my_list) -> a separate copy")
_register("wait", b_wait, 1, 1, "wait(0.5) -> pause for half a second")
