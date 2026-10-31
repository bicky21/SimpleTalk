"""Step 3: walk through the tree of nodes and actually run the program."""

import math
import sys

from . import nodes as N
from .builtins import BUILTINS
from .errors import RuntimeProblem, SimpleTalkError, did_you_mean
from .values import Builtin, Function, equal, is_number, show, tidy_number, type_name

MAX_CALL_DEPTH = 1000

# Words people bring from other languages, and what to use instead.
FRIENDLY_RENAMES = {
    "print": "say", "echo": "say", "input": "ask ... into ...",
    "len": "length", "str": "text", "int": "number", "float": "number",
    "append": "add ... to ...", "push": "add ... to ...", "def": "define",
    "function": "define", "while": "repeat while", "loop": "repeat",
    "True": "true", "False": "false", "None": "nothing", "null": "nothing",
    "elif": "else if", "break": "stop", "continue": "skip",
}


class _Stop(Exception):
    pass


class _Skip(Exception):
    pass


class _Return(Exception):
    def __init__(self, value):
        self.value = value


class Scope:
    """A box of variables. Functions get their own box that can see the outer one."""

    def __init__(self, parent=None):
        self.vars = {}
        self.parent = parent

    def find(self, name):
        scope = self
        while scope is not None:
            if name in scope.vars:
                return scope
            scope = scope.parent
        return None

    def all_names(self):
        names = set()
        scope = self
        while scope is not None:
            names.update(scope.vars)
            scope = scope.parent
        return names


class Interpreter:
    def __init__(self, output=None, input_fn=None):
        self.output = output or (lambda text: print(text, flush=True))
        self.input_fn = input_fn or input
        self.builtins = Scope()
        self.builtins.vars.update(BUILTINS)
        self.globals = Scope(self.builtins)
        self.depth = 0

    # ------------------------------------------------------------- running
    def run(self, program):
        old_limit = sys.getrecursionlimit()
        sys.setrecursionlimit(max(old_limit, 50_000))
        try:
            self.exec_block(program, self.globals)
        except RecursionError:
            raise RuntimeProblem("The program went too deep (too many nested calls).",
                                 hint="Check that every function that calls itself has a way to stop.")
        finally:
            sys.setrecursionlimit(old_limit)

    def exec_block(self, body, scope):
        for stmt in body:
            self.execute(stmt, scope)

    def execute(self, node, scope):
        try:
            getattr(self, "exec_" + type(node).__name__)(node, scope)
        except SimpleTalkError as err:
            if err.line is None:
                err.line, err.column = node.line, node.column
            raise

    def fail(self, node, message, hint=None):
        raise RuntimeProblem(message, node.line, node.column, hint)

    # ------------------------------------------------------------- statements
    def exec_Say(self, node, scope):
        self.output(" ".join(show(self.eval(v, scope)) for v in node.values))

    def exec_Ask(self, node, scope):
        prompt = show(self.eval(node.prompt, scope))
        if prompt and not prompt.endswith(" "):
            prompt += " "
        try:
            answer = self.input_fn(prompt)
        except EOFError:
            answer = ""
        answer = answer.strip()
        # Numbers typed by the user become real numbers automatically.
        value = answer
        try:
            value = int(answer)
        except ValueError:
            try:
                f = float(answer)
                if math.isfinite(f) and answer.lower() not in ("nan", "inf", "infinity"):
                    value = tidy_number(f)
            except ValueError:
                pass
        self.assign(node.target, value, scope)

    def assign(self, name, value, scope):
        """`set` updates the nearest existing variable, or creates a new one here."""
        target = scope.find(name)
        if target is None or target is self.builtins:
            target = scope
        target.vars[name] = value

    def exec_Set(self, node, scope):
        value = self.eval(node.value, scope)
        if isinstance(node.target, N.Name):
            self.assign(node.target.name, value, scope)
            return
        container = self.eval(node.target.target, scope)
        index = self.eval(node.target.index, scope)
        if isinstance(container, str):
            self.fail(node, "Text can't be changed one letter at a time.",
                      hint="Build a new text instead, e.g. with replace(...).")
        if not isinstance(container, list):
            self.fail(node, f"Only lists can be changed with [ ], not {type_name(container)}.")
        pos = self.position(node.target, container, index)
        container[pos] = value

    def exec_Change(self, node, scope):
        owner = scope.find(node.name)
        if owner is None or owner is self.builtins:
            self.fail(node, f"I can't change '{node.name}' because it doesn't exist yet.",
                      hint=f"Create it first: set {node.name} to 0")
        current = owner.vars[node.name]
        amount = self.eval(node.amount, scope)
        if not is_number(current):
            self.fail(node, f"'{node.name}' is {type_name(current)}, so I can't change it by a number.")
        if not is_number(amount):
            self.fail(node, f"I can only change '{node.name}' by a number, not {type_name(amount)}.")
        owner.vars[node.name] = tidy_number(current + amount)

    def exec_Add(self, node, scope):
        value = self.eval(node.value, scope)
        target = self.eval(node.target, scope)
        if not isinstance(target, list):
            hint = None
            if is_number(target) and isinstance(node.target, N.Name):
                hint = f"To add to a number, write: change {node.target.name} by {show(value)}"
            self.fail(node, f"'add ... to' needs a list, but this is {type_name(target)}.", hint)
        target.append(value)

    def exec_Remove(self, node, scope):
        value = self.eval(node.value, scope)
        target = self.eval(node.target, scope)
        if not isinstance(target, list):
            self.fail(node, f"'remove ... from' needs a list, but this is {type_name(target)}.")
        for i, item in enumerate(target):
            if equal(item, value):
                del target[i]
                return
        self.fail(node, f"{show(value, True)} is not in the list, so I can't remove it.",
                  hint="Check first with: if ... in my_list")

    def exec_If(self, node, scope):
        for cond, body in node.branches:
            if self.truth(cond, scope, "if"):
                self.exec_block(body, scope)
                return
        if node.else_body is not None:
            self.exec_block(node.else_body, scope)

    def run_loop_body(self, body, scope):
        """Run one pass of a loop. Returns False if the loop should stop."""
        try:
            self.exec_block(body, scope)
        except _Skip:
            pass
        except _Stop:
            return False
        return True

    def exec_RepeatTimes(self, node, scope):
        count = self.eval(node.count, scope)
        if not is_number(count) or (isinstance(count, float) and not count.is_integer()):
            self.fail(node, f"'repeat' needs a whole number of times, not {show(count, True)}.")
        if count < 0:
            self.fail(node, f"I can't repeat something {show(count)} times.")
        for _ in range(int(count)):
            if not self.run_loop_body(node.body, scope):
                break

    def exec_RepeatWhile(self, node, scope):
        while True:
            if node.condition is not None:
                ok = self.truth(node.condition, scope, "repeat until" if node.until else "repeat while")
                if ok == node.until:
                    break
            if not self.run_loop_body(node.body, scope):
                break

    def exec_ForEach(self, node, scope):
        items = self.eval(node.iterable, scope)
        if isinstance(items, str):
            items = list(items)
        elif isinstance(items, list):
            items = list(items)        # loop over a copy, so changing the list is safe
        else:
            self.fail(node, f"'for each' needs a list or text, but got {type_name(items)}.",
                      hint="To count, use: for i from 1 to 10")
        for item in items:
            scope.vars[node.var] = item
            if not self.run_loop_body(node.body, scope):
                break

    def exec_ForRange(self, node, scope):
        start = self.eval(node.start, scope)
        end = self.eval(node.end, scope)
        for v, which in ((start, "start"), (end, "end")):
            if not is_number(v):
                self.fail(node, f"The {which} of 'for ... from ... to' must be a number, not {type_name(v)}.")
        step = 1 if end >= start else -1     # counts down automatically
        i = start
        while (i <= end) if step > 0 else (i >= end):
            scope.vars[node.var] = i
            if not self.run_loop_body(node.body, scope):
                break
            i = tidy_number(i + step)

    def exec_Define(self, node, scope):
        scope.vars[node.name] = Function(node.name, node.params, node.body, scope)

    def exec_Return(self, node, scope):
        value = None if node.value is None else self.eval(node.value, scope)
        raise _Return(value)

    def exec_Stop(self, node, scope):
        raise _Stop()

    def exec_Skip(self, node, scope):
        raise _Skip()

    def exec_ExprStatement(self, node, scope):
        self.eval(node.expr, scope)

    # ------------------------------------------------------------- expressions
    def eval(self, node, scope):
        try:
            return getattr(self, "eval_" + type(node).__name__)(node, scope)
        except SimpleTalkError as err:
            if err.line is None:
                err.line, err.column = node.line, node.column
            raise

    def truth(self, node, scope, where):
        value = self.eval(node, scope)
        if isinstance(value, bool):
            return value
        self.fail(node, f"'{where}' needs true or false, but got {type_name(value)} {show(value, True)}.",
                  hint="Compare it with something, like: x > 0  or  name is \"\"")

    def eval_Literal(self, node, scope):
        return node.value

    def eval_Text(self, node, scope):
        return "".join(p if isinstance(p, str) else show(self.eval(p, scope)) for p in node.parts)

    def eval_ListLiteral(self, node, scope):
        return [self.eval(item, scope) for item in node.items]

    def eval_Name(self, node, scope):
        owner = scope.find(node.name)
        if owner is not None:
            return owner.vars[node.name]
        hint = None
        if node.name in FRIENDLY_RENAMES:
            hint = f"In SimpleTalk, use '{FRIENDLY_RENAMES[node.name]}' instead of '{node.name}'."
        else:
            hint = did_you_mean(node.name, scope.all_names()) or \
                f"Give it a value first, like: set {node.name} to 0"
        self.fail(node, f"I don't know what '{node.name}' is.", hint)

    def eval_Unary(self, node, scope):
        if node.op == "not":
            return not self.truth(node.operand, scope, "not")
        value = self.eval(node.operand, scope)
        if not is_number(value):
            self.fail(node, f"I can't make {type_name(value)} negative.")
        return -value

    def eval_Binary(self, node, scope):
        op = node.op
        if op in ("and", "or"):
            left = self.truth(node.left, scope, op)
            if op == "and" and not left:
                return False
            if op == "or" and left:
                return True
            return self.truth(node.right, scope, op)

        a = self.eval(node.left, scope)
        b = self.eval(node.right, scope)

        if op == "=":
            return equal(a, b)
        if op == "!=":
            return not equal(a, b)
        if op == "in":
            if isinstance(b, list):
                return any(equal(a, item) for item in b)
            if isinstance(b, str):
                if not isinstance(a, str):
                    self.fail(node, f"To look inside text, the thing to find must be text too, not {type_name(a)}.")
                return a in b
            self.fail(node, f"'in' needs a list or text on the right, not {type_name(b)}.")
        if op in ("<", ">", "<=", ">="):
            if not ((is_number(a) and is_number(b)) or (isinstance(a, str) and isinstance(b, str))):
                self.fail(node, f"I can't compare {type_name(a)} with {type_name(b)} using '{op}'.",
                          hint="Compare numbers with numbers, or text with text. number(...) can help.")
            return {"<": a < b, ">": a > b, "<=": a <= b, ">=": a >= b}[op]

        if op == "+":
            if is_number(a) and is_number(b):
                return tidy_number(a + b)
            if isinstance(a, str) or isinstance(b, str):
                return show(a) + show(b)        # "Age: " + 12 -> "Age: 12"
            if isinstance(a, list) and isinstance(b, list):
                return a + b
            self.fail(node, f"I can't add {type_name(a)} and {type_name(b)}.")

        if not (is_number(a) and is_number(b)):
            names = {"-": "subtract", "*": "multiply", "/": "divide", "mod": "use mod with"}
            hint = None
            if isinstance(a, str) or isinstance(b, str):
                hint = "If the text holds a number, turn it into one with number(...)."
            self.fail(node, f"I can only {names[op]} numbers, not {type_name(a)} and {type_name(b)}.", hint)
        try:
            if op == "-":
                return tidy_number(a - b)
            if op == "*":
                return tidy_number(a * b)
            if op == "/":
                if b == 0:
                    self.fail(node, "You can't divide by zero.")
                if isinstance(a, int) and isinstance(b, int) and a % b == 0:
                    return a // b
                return tidy_number(a / b)
            if op == "mod":
                if b == 0:
                    self.fail(node, "You can't use mod with zero.")
                return tidy_number(a % b)
        except OverflowError:
            self.fail(node, "That number is too big for me to work with.")
        raise AssertionError(f"unknown operator {op}")

    def position(self, node, container, index):
        """Turn a 1-based (or negative, from the end) index into a Python index."""
        if not is_number(index) or (isinstance(index, float) and not index.is_integer()):
            self.fail(node, f"Positions must be whole numbers, not {show(index, True)}.")
        index = int(index)
        size = len(container)
        if index == 0:
            self.fail(node, "Positions start at 1 in SimpleTalk, so [0] doesn't exist.",
                      hint="Use [1] for the first item and [-1] for the last.")
        if index > size or index < -size:
            what = "list" if isinstance(container, list) else "text"
            self.fail(node, f"Position {index} is outside the {what}, which has {size} item"
                            f"{'' if size == 1 else 's'}.")
        return index - 1 if index > 0 else size + index

    def eval_Index(self, node, scope):
        container = self.eval(node.target, scope)
        index = self.eval(node.index, scope)
        if not isinstance(container, (list, str)):
            self.fail(node, f"Only lists and text have positions, not {type_name(container)}.")
        return container[self.position(node, container, index)]

    def eval_Call(self, node, scope):
        fn = self.eval(node.callee, scope)
        args = [self.eval(a, scope) for a in node.args]
        name = node.callee.name if isinstance(node.callee, N.Name) else "this function"

        if isinstance(fn, Builtin):
            if len(args) < fn.min_args or (fn.max_args is not None and len(args) > fn.max_args):
                self.fail(node, f"{fn.name}() got {len(args)} value{'s' if len(args) != 1 else ''}"
                                f" but needs {self.arity_text(fn.min_args, fn.max_args)}.",
                          hint=f"Example: {fn.usage}")
            try:
                return fn.fn(*args)
            except RuntimeProblem as err:
                if err.line is None:
                    err.line, err.column = node.line, node.column
                raise

        if not isinstance(fn, Function):
            self.fail(node, f"'{name}' is {type_name(fn)}, not a function, so it can't be called with ( ).")

        if len(args) != len(fn.params):
            params = ", ".join(fn.params)
            self.fail(node, f"{fn.name}() needs {len(fn.params)} value{'s' if len(fn.params) != 1 else ''}"
                            f" ({params}) but got {len(args)}.")

        if self.depth >= MAX_CALL_DEPTH:
            self.fail(node, f"Too many functions calling each other (more than {MAX_CALL_DEPTH} deep).",
                      hint=f"Does '{fn.name}' keep calling itself forever? Make sure it has a way to stop.")
        local = Scope(fn.closure)
        local.vars.update(zip(fn.params, args))
        self.depth += 1
        try:
            self.exec_block(fn.body, local)
        except _Return as ret:
            return ret.value
        finally:
            self.depth -= 1
        return None

    @staticmethod
    def arity_text(lo, hi):
        if hi is None:
            return f"at least {lo}"
        if lo == hi:
            return f"exactly {lo}"
        return f"{lo} to {hi}"
