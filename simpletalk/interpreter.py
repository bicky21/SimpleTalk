"""Step 3: walk through the tree of nodes and actually run the program."""

import json
import math
import os
import threading
import time

from . import nodes as N
from .builtins import BUILTINS
from .runner import run_protected, start_thread
from .errors import RuntimeProblem, SimpleTalkError, UserProblem, did_you_mean
from .values import (Builtin, Function, TaskValue, equal, is_number, show, tidy_number,
                     type_name)

MAX_CALL_DEPTH = 1000

# Words people bring from other languages, and what to use instead.
FRIENDLY_RENAMES = {
    "say": "out", "print": "out", "input": "in name \"prompt\"", "ask": "in name \"prompt\"",
    "length": "len", "str": "txt", "text": "txt", "int": "num", "float": "num", "number": "num",
    "random": "rand", "reverse": "rev", "power": "pow", "replace": "swap",
    "is_number": "isnum", "append": "add list value", "push": "add list value",
    "True": "true", "False": "false", "None": "none", "nothing": "none", "null": "none", "nil": "none",
}
RANGE_LIMIT = 10_000_000


_MISSING = object()


def to_json(value):
    """SimpleTalk value -> something json can write. Raises ValueError for functions/tasks."""
    if value is None or isinstance(value, (bool, int, float, str)):
        if isinstance(value, float) and not math.isfinite(value):
            raise ValueError("not a finite number")
        return value
    if isinstance(value, list):
        return [to_json(v) for v in value]
    if isinstance(value, dict):
        return {str(k): to_json(v) for k, v in value.items()}
    raise ValueError(type_name(value))


def from_json(value):
    """json value -> SimpleTalk value (2.0 becomes 2, like everywhere else)."""
    if isinstance(value, list):
        return [from_json(v) for v in value]
    if isinstance(value, dict):
        return {str(k): from_json(v) for k, v in value.items()}
    return tidy_number(value) if isinstance(value, float) else value


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
    def __init__(self, output=None, input_fn=None, trace=None, program_path=None):
        self.output = output or (lambda text: print(text, flush=True))
        self.input_fn = input_fn or input
        self.builtins = Scope()
        self.builtins.vars.update(BUILTINS)
        self.globals = Scope(self.builtins)
        self._local = threading.local()     # call depth is counted per task
        self.program_path = os.path.abspath(program_path) if program_path else None
        # Files named in read(), load(), use ... are found next to the program.
        self.base_dir = os.path.dirname(self.program_path) if program_path else os.getcwd()
        self.root_dir = self.base_dir       # file names in messages are shown relative to this
        self.modules = {}                   # `use`: files already loaded
        self.loading = []                   # `use`: files being loaded (to spot loops)
        self.kept = {}                      # `keep`: name -> scope that holds it
        self.memory = None                  # `keep`: values saved by earlier runs
        self.tasks = []                     # `task`: everything started
        self.tests_lock = threading.Lock()
        self.source = None                  # the file being run right now (for error messages)
        self.filename = None
        self.add_file_builtins()
        self.watched = set()        # names reported by `watch`
        self.tests_passed = 0       # counted by `test`
        self.trace = trace          # function(line_number) called before each step
        self.interrupted = False    # set by Ctrl+C; the program stops at its next step

    # ------------------------------------------------------------- running
    def run(self, program):
        """Run a parsed program (on a big-stack worker thread, see runner.py)."""
        def whole_program():
            try:
                self._guarded(self.exec_block, program, self.globals)
                self.finish_tasks()
            finally:
                self.save_memory()
        run_protected(self, whole_program)

    @property
    def depth(self):
        return getattr(self._local, "depth", 0)

    @depth.setter
    def depth(self, value):
        self._local.depth = value

    def evaluate(self, expr):
        """Work out one expression in the global scope (used by the playground)."""
        return run_protected(self, lambda: self._guarded(self.eval, expr, self.globals))

    @staticmethod
    def _guarded(fn, *args):
        try:
            return fn(*args)
        except RecursionError:
            raise RuntimeProblem("The program went too deep (too many nested calls).",
                                 hint="Check that every function that calls itself has a way to stop.")

    def exec_block(self, body, scope):
        for stmt in body:
            self.execute(stmt, scope)

    def execute(self, node, scope):
        if self.interrupted:
            raise KeyboardInterrupt
        if self.trace is not None:
            self.trace(node.line)
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

    def read_answer(self, prompt, node):
        try:
            return self.input_fn(prompt).strip()
        except EOFError:
            if getattr(node, "kind", None):
                self.fail(node, "The program asked a question, but no answer was typed.")
            return ""

    @staticmethod
    def as_number(answer):
        try:
            return int(answer)
        except ValueError:
            pass
        try:
            f = float(answer)
            if math.isfinite(f) and answer.lower() not in ("nan", "inf", "infinity"):
                return tidy_number(f)
        except ValueError:
            pass
        return None

    YES = {"y", "yes", "true", "ok", "sure", "haan", "ha"}
    NO = {"n", "no", "false", "nope", "nahi", "na"}

    def exec_Ask(self, node, scope):
        prompt = "" if node.prompt is None else show(self.eval(node.prompt, scope))
        if prompt and not prompt.endswith(" "):
            prompt += " "
        while True:
            answer = self.read_answer(prompt, node)
            if node.kind == "num":
                value = self.as_number(answer)
                if value is not None:
                    break
                self.output("Please type a number.")
            elif node.kind == "yes":
                if answer.lower() in self.YES:
                    value = True
                    break
                if answer.lower() in self.NO:
                    value = False
                    break
                self.output("Please answer yes or no.")
            else:
                # Plain `in`: a typed number becomes a real number, anything else stays text.
                number = self.as_number(answer)
                value = answer if number is None else number
                break
        self.assign(node.target, value, scope, node)

    def assign(self, name, value, scope, node=None):
        """`let` updates the nearest existing variable, or creates a new one here."""
        target = scope.find(name)
        if target is None or target is self.builtins:
            target = scope
        old = target.vars.get(name, _MISSING)
        target.vars[name] = value
        if name in self.watched and node is not None:
            self.report(name, old, value, node)

    def report(self, name, old, new, node):
        """Used by `watch`: tell the user a watched variable changed."""
        if old is _MISSING:
            self.output(f"[watch] line {node.line}: {name} = {show(new, True)}")
        else:
            self.output(f"[watch] line {node.line}: {name} = {show(new, True)}  (was {show(old, True)})")

    def report_list(self, target_node, node, scope):
        """A watched list was changed in place (add, del, let list[i])."""
        root = target_node
        while isinstance(root, (N.Index, N.Field)):
            root = root.target
        if isinstance(root, N.Name) and root.name in self.watched:
            self.output(f"[watch] line {node.line}: {root.name} = {show(self.eval(root, scope), True)}")

    def exec_Set(self, node, scope):
        value = self.eval(node.value, scope)
        if isinstance(node.target, N.Name):
            self.assign(node.target.name, value, scope, node)
            return
        if isinstance(node.target, N.Field):
            container = self.eval(node.target.target, scope)
            if not isinstance(container, dict):
                self.fail(node, f"Only maps have named fields, not {type_name(container)}.",
                          hint='Make a map first, like: let me {name: "Bicky"}')
            container[node.target.name] = value
            self.report_list(node.target, node, scope)
            return
        container = self.eval(node.target.target, scope)
        index = self.eval(node.target.index, scope)
        if isinstance(container, dict):
            container[self.map_key(node.target, index)] = value
            self.report_list(node.target, node, scope)
            return
        if isinstance(container, str):
            self.fail(node, "Text can't be changed one letter at a time.",
                      hint="Build a new text instead, e.g. with swap(...).")
        if not isinstance(container, list):
            self.fail(node, f"Only lists can be changed with [ ], not {type_name(container)}.")
        pos = self.position(node.target, container, index)
        container[pos] = value
        self.report_list(node.target, node, scope)

    def exec_Change(self, node, scope):
        owner = scope.find(node.name)
        if owner is None or owner is self.builtins:
            self.fail(node, f"I can't use 'up' on '{node.name}' because it doesn't exist yet.",
                      hint=f"Create it first: let {node.name} 0")
        current = owner.vars[node.name]
        amount = self.eval(node.amount, scope)
        if not is_number(current):
            self.fail(node, f"'{node.name}' is {type_name(current)}, so 'up' can't add a number to it.")
        if not is_number(amount):
            self.fail(node, f"'up' needs a number to add to '{node.name}', not {type_name(amount)}.")
        owner.vars[node.name] = tidy_number(current + amount)
        if node.name in self.watched:
            self.report(node.name, current, owner.vars[node.name], node)

    def exec_Add(self, node, scope):
        value = self.eval(node.value, scope)
        target = self.eval(node.target, scope)
        if isinstance(target, dict):
            self.fail(node, "'add' puts items into lists. To add to a map, give the key a value.",
                      hint="Like: let me.city \"Kolkata\"")
        if not isinstance(target, list):
            hint = None
            if is_number(target) and isinstance(node.target, N.Name):
                hint = f"To add to a number, write: up {node.target.name} {show(value)}"
            self.fail(node, f"'add' needs a list, but this is {type_name(target)}.", hint)
        target.append(value)
        self.report_list(node.target, node, scope)

    def exec_Remove(self, node, scope):
        value = self.eval(node.value, scope)
        target = self.eval(node.target, scope)
        if isinstance(target, dict):
            key = self.map_key(node, value)
            if key not in target:
                self.fail(node, f"The map has no key '{key}', so I can't delete it.",
                          hint=did_you_mean(key, target.keys()))
            del target[key]
            self.report_list(node.target, node, scope)
            return
        if not isinstance(target, list):
            self.fail(node, f"'del' needs a list or a map, but this is {type_name(target)}.")
        for i, item in enumerate(target):
            if equal(item, value):
                del target[i]
                self.report_list(node.target, node, scope)
                return
        self.fail(node, f"{show(value, True)} is not in the list, so I can't delete it.",
                  hint="Check first with: when my_list has ...")

    def exec_Watch(self, node, scope):
        for name in node.names:
            self.watched.add(name)
            owner = scope.find(name)
            if owner is not None and owner is not self.builtins:
                self.output(f"[watch] line {node.line}: watching {name}, now {show(owner.vars[name], True)}")
            else:
                self.output(f"[watch] line {node.line}: watching {name} (not set yet)")

    def exec_Test(self, node, scope):
        expr = node.expr
        if isinstance(expr, N.Binary) and expr.op in ("=", "!=", "<", ">", "<=", ">=", "has"):
            left = self.eval(expr.left, scope)
            right = self.eval(expr.right, scope)
            ok = self.eval(N.Binary(expr.op, N.Literal(left), N.Literal(right),
                                    line=expr.line, column=expr.column), scope)
            if not ok:
                self.fail(node, f"Test failed: {node.text}",
                          hint=f"The left side is {show(left, True)} and the right side is {show(right, True)}.")
        else:
            value = self.eval(expr, scope)
            if not isinstance(value, bool):
                self.fail(node, f"'test' needs something that is true or false, but got {type_name(value)}.",
                          hint="Write a check, like: test square(3) = 9")
            if not value:
                self.fail(node, f"Test failed: {node.text}", hint="This was false.")
        with self.tests_lock:
            self.tests_passed += 1

    # ---------------------------------------------------------- problems
    def exec_Try(self, node, scope):
        try:
            self.exec_block(node.body, scope)
        except RuntimeProblem as err:
            if node.err_name:
                self.assign(node.err_name, err.message, scope, node)
            self.exec_block(node.handler, scope)

    def exec_Oops(self, node, scope):
        message = show(self.eval(node.message, scope))
        raise UserProblem(message, node.line, node.column)

    # ---------------------------------------------------------- pick
    def exec_Pick(self, node, scope):
        value = self.eval(node.value, scope)
        for patterns, body in node.cases:
            if any(self.matches(value, p, scope) for p in patterns):
                self.exec_block(body, scope)
                return
        if node.else_body is not None:
            self.exec_block(node.else_body, scope)

    def matches(self, value, pattern, scope):
        if isinstance(pattern, N.Binary) and pattern.op == "..":
            low, high = self.range_ends(pattern, scope)
            low, high = min(low, high), max(low, high)
            return is_number(value) and low <= value <= high
        return equal(value, self.eval(pattern, scope))

    # ---------------------------------------------------------- use
    def exec_Use(self, node, scope):
        name = self.eval(node.path, scope)
        if not isinstance(name, str):
            self.fail(node, "'use' needs a file name in quotes.")
        path = self.resolve(name)
        if not os.path.splitext(path)[1]:
            path += ".simp"
        if path in self.loading:
            self.fail(node, f"'{name}' uses itself (through other files), which would never finish.",
                      hint="Move the shared code into a third file that both can use.")
        if path not in self.modules:
            try:
                with open(path, encoding="utf-8-sig") as f:
                    source = f.read()
            except FileNotFoundError:
                self.fail(node, f"I can't find the file '{name}'.",
                          hint=f"It should be in the same folder as your program: {self.base_dir}")
            except (OSError, UnicodeDecodeError) as err:
                self.fail(node, f"I can't read '{name}': {err}")
            from .lexer import tokenize
            from .parser import Parser
            module_scope = Scope(self.builtins)
            saved = (self.base_dir, self.source, self.filename)
            self.loading.append(path)
            self.base_dir = os.path.dirname(path)
            self.source, self.filename = source, self.short_name(path)
            try:
                program = Parser(tokenize(source), source).parse_program()
                self.exec_block(program, module_scope)
            except SimpleTalkError as err:
                if err.source is None:
                    err.source, err.filename = source, self.short_name(path)
                raise
            finally:
                self.base_dir, self.source, self.filename = saved
                self.loading.pop()
            self.modules[path] = module_scope
        for key, value in self.modules[path].vars.items():
            if not key.startswith("_"):
                scope.vars[key] = value

    def short_name(self, path):
        try:
            rel = os.path.relpath(path, self.root_dir)
        except ValueError:                  # another drive on Windows
            return path
        return path if rel.startswith("..") else rel

    def resolve(self, name):
        return os.path.normpath(os.path.join(self.base_dir, os.path.expanduser(name)))

    # ---------------------------------------------------------- keep
    def memory_file(self):
        if self.program_path is None:
            return None
        return os.path.splitext(self.program_path)[0] + ".memory.json"

    def exec_Keep(self, node, scope):
        if self.memory is None:
            self.memory = {}
            path = self.memory_file()
            if path and os.path.exists(path):
                try:
                    with open(path, encoding="utf-8") as f:
                        data = json.load(f)
                    if isinstance(data, dict):
                        self.memory = data
                except (OSError, ValueError):
                    self.output(f"[keep] {os.path.basename(path)} is damaged, starting fresh.")
        if node.name in self.memory:
            value = from_json(self.memory[node.name])
        else:
            value = self.eval(node.default, scope)
        scope.vars[node.name] = value
        self.kept[node.name] = scope
        if node.name in self.watched:
            self.report(node.name, _MISSING, value, node)

    def save_memory(self):
        path = self.memory_file()
        if not self.kept or path is None:
            return
        data = dict(self.memory or {})
        for name, scope in self.kept.items():
            try:
                data[name] = to_json(scope.vars.get(name))
            except ValueError:
                self.output(f"[keep] {name} holds a {type_name(scope.vars.get(name))}, which can't be saved.")
        try:
            tmp = path + ".tmp"
            with open(tmp, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            os.replace(tmp, path)              # never leaves a half-written file
        except OSError as err:
            self.output(f"[keep] Couldn't save remembered values: {err}")

    # ---------------------------------------------------------- tasks
    def exec_Task(self, node, scope):
        task = TaskValue(node.name)
        local = Scope(scope)

        def work():
            try:
                self.depth = 0
                self.exec_block(node.body, local)
            except _Return as ret:
                task.result = ret.value
            except BaseException as err:        # kept for `await`
                task.error = err
            finally:
                task.done.set()

        self.tasks.append(task)
        scope.vars[node.name] = task
        if start_thread(work, name=f"task-{node.name}") is None:
            work()                              # can't start threads here: run it now

    def wait_for(self, task):
        while not task.done.wait(0.05):
            if self.interrupted:
                raise KeyboardInterrupt

    def finish_tasks(self):
        """At the end of the program, wait for running tasks and report their problems."""
        for task in list(self.tasks):
            self.wait_for(task)
            if task.error is not None and not task.awaited:
                task.awaited = True
                raise task.error

    # ---------------------------------------------------------- files
    def add_file_builtins(self):
        def read(path):
            p = self.file_path("read", path)
            try:
                with open(p, encoding="utf-8-sig") as f:
                    return f.read()
            except FileNotFoundError:
                raise RuntimeProblem(f"read() can't find the file '{path}'.",
                                     hint="Check the name, or test first with exists(...).")
            except (OSError, UnicodeDecodeError) as err:
                raise RuntimeProblem(f"read() can't open '{path}': {err}")

        def write(path, text):
            p = self.file_path("write", path)
            try:
                with open(p, "w", encoding="utf-8") as f:
                    f.write(text if isinstance(text, str) else show(text))
            except OSError as err:
                raise RuntimeProblem(f"write() can't save '{path}': {err}")

        def load(path):
            text = read(path)
            try:
                return from_json(json.loads(text))
            except ValueError as err:
                raise RuntimeProblem(f"load() found a mistake in the JSON file '{path}': {err}")

        def save(path, value):
            try:
                text = json.dumps(to_json(value), indent=2, ensure_ascii=False)
            except ValueError:
                raise RuntimeProblem(f"save() can't store a {type_name(value)} in a JSON file.",
                                     hint="Numbers, text, true/false, none, lists and maps can be saved.")
            write(path, text)

        def exists(path):
            return os.path.exists(self.file_path("exists", path))

        def wait(seconds):
            if not is_number(seconds) or seconds < 0:
                raise RuntimeProblem("wait() needs a number of seconds that isn't negative.")
            end = time.monotonic() + seconds
            while True:                          # small steps, so Ctrl+C works
                left = end - time.monotonic()
                if left <= 0:
                    return None
                if self.interrupted:
                    raise KeyboardInterrupt
                time.sleep(min(left, 0.05))

        for name, fn, lo, hi, usage in [
            ("read", read, 1, 1, 'read("notes.txt") -> the text in the file'),
            ("write", write, 2, 2, 'write("notes.txt", "hello") -> saves the text'),
            ("load", load, 1, 1, 'load("data.json") -> lists and maps'),
            ("save", save, 2, 2, 'save("data.json", my_map) -> writes JSON'),
            ("exists", exists, 1, 1, 'exists("notes.txt") -> true or false'),
            ("wait", wait, 1, 1, "wait(0.5) -> pause for half a second"),
        ]:
            self.builtins.vars[name] = Builtin(name, fn, lo, hi, usage)

    def file_path(self, fn, path):
        if not isinstance(path, str) or not path:
            raise RuntimeProblem(f"{fn}() needs a file name in quotes, like \"notes.txt\".")
        return self.resolve(path)

    def exec_If(self, node, scope):
        for cond, body in node.branches:
            if self.truth(cond, scope, "when"):
                self.exec_block(body, scope)
                return
        if node.else_body is not None:
            self.exec_block(node.else_body, scope)

    def run_loop_body(self, body, scope):
        """Run one pass of a loop. Returns False if the loop should stop."""
        if self.interrupted:
            raise KeyboardInterrupt
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
            hint = None
            if isinstance(count, list):
                hint = "To go through a list, give the loop a name: loop item my_list"
            self.fail(node, f"'loop' needs a whole number of times, not {show(count, True)}.", hint)
        if count < 0:
            self.fail(node, f"I can't loop {show(count)} times.")
        for _ in range(int(count)):
            if not self.run_loop_body(node.body, scope):
                break

    def exec_RepeatWhile(self, node, scope):
        while True:
            if node.condition is not None:
                ok = self.truth(node.condition, scope, "loop while")
                if not ok:
                    break
            if not self.run_loop_body(node.body, scope):
                break

    def exec_ForEach(self, node, scope):
        it = node.iterable
        if isinstance(it, N.Binary) and it.op == "..":
            items = self.range_iter(it, scope)           # counts without building a list
        else:
            items = self.eval(it, scope)
            if isinstance(items, (str, list, dict)):
                items = list(items)    # loop over a copy (a map gives its keys)
            else:
                self.fail(node, f"'loop {node.var} ...' needs a list, text or range, but got {type_name(items)}.",
                          hint=f"To count, use a range: loop {node.var} 1..10")
        for item in items:
            old = scope.vars.get(node.var, _MISSING)
            scope.vars[node.var] = item
            if node.var in self.watched:
                self.report(node.var, old, item, node)
            if not self.run_loop_body(node.body, scope):
                break

    def range_ends(self, node, scope):
        start = self.eval(node.left, scope)
        end = self.eval(node.right, scope)
        for v, which in ((start, "start"), (end, "end")):
            if not is_number(v):
                self.fail(node, f"The {which} of a range must be a number, not {type_name(v)}.",
                          hint="Ranges look like: 1..10")
        return start, end

    def range_iter(self, node, scope):
        start, end = self.range_ends(node, scope)
        step = 1 if end >= start else -1     # 5..1 counts down
        i = start
        while (i <= end) if step > 0 else (i >= end):
            yield i
            i = tidy_number(i + step)

    def eval_range(self, node, scope):
        start, end = self.range_ends(node, scope)
        if abs(end - start) >= RANGE_LIMIT:
            self.fail(node, f"That range is too big to turn into a list (over {RANGE_LIMIT:,} items).",
                      hint="Loop over it directly instead: loop i 1..n")
        return list(self.range_iter(node, scope))

    def exec_Define(self, node, scope):
        scope.vars[node.name] = Function(node.name, node.params, node.body, scope,
                                         self.source, self.filename)

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
                  hint="Compare it with something, like: x > 0  or  name != \"\"")

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
                f"Give it a value first, like: let {node.name} 0"
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
        if op == "..":
            return self.eval_range(node, scope)
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
        if op == "has":
            if isinstance(a, dict):
                return isinstance(b, str) and b in a
            if isinstance(a, list):
                return any(equal(b, item) for item in a)
            if isinstance(a, str):
                if not isinstance(b, str):
                    self.fail(node, f"To look inside text, the thing to find must be text too, not {type_name(b)}.")
                return b in a
            self.fail(node, f"'has' needs a list or text on the left, not {type_name(a)}.",
                      hint='Like: fruits has "kiwi"   or   "hello" has "ell"')
        if op in ("<", ">", "<=", ">="):
            if not ((is_number(a) and is_number(b)) or (isinstance(a, str) and isinstance(b, str))):
                self.fail(node, f"I can't compare {type_name(a)} with {type_name(b)} using '{op}'.",
                          hint="Compare numbers with numbers, or text with text. num(...) can help.")
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
                hint = "If the text holds a number, turn it into one with num(...)."
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
        if isinstance(container, dict):
            return self.map_get(node, container, self.map_key(node, index))
        if not isinstance(container, (list, str)):
            self.fail(node, f"Only lists, text and maps can use [ ], not {type_name(container)}.")
        return container[self.position(node, container, index)]

    def map_key(self, node, key):
        if not isinstance(key, str):
            self.fail(node, f"Map keys are text, so [{show(key, True)}] doesn't work here.",
                      hint='Use text, like: me["name"]  or the short way: me.name')
        return key

    def map_get(self, node, m, key):
        if key not in m:
            self.fail(node, f"This map has no '{key}'.",
                      hint=did_you_mean(key, m.keys()) or f"Check first with: when my_map has \"{key}\"")
        return m[key]

    def eval_Field(self, node, scope):
        container = self.eval(node.target, scope)
        if not isinstance(container, dict):
            hint = None
            if isinstance(container, list):
                hint = "Lists use positions, like: my_list[1]"
            self.fail(node, f"Only maps have named fields like .{node.name}, not {type_name(container)}.", hint)
        return self.map_get(node, container, node.name)

    def eval_MapLiteral(self, node, scope):
        return {key: self.eval(value, scope) for key, value in node.items}

    def eval_Lambda(self, node, scope):
        body = [N.Return(node.body, line=node.line, column=node.column)]
        return Function("(fn)", node.params, body, scope, self.source, self.filename)

    def eval_Pipe(self, node, scope):
        value = self.eval(node.value, scope)
        for stage in node.stages:
            if stage[0] in ("only", "each"):
                word, expr = stage
                if isinstance(value, str):
                    value = list(value)
                if not isinstance(value, list):
                    self.fail(expr, f"'| {word}' works on lists, but got {type_name(value)}.")
                item_scope = Scope(scope)
                results = []
                for item in value:
                    item_scope.vars["it"] = item
                    if word == "each":
                        results.append(self.eval(expr, item_scope))
                    elif self.truth(expr, item_scope, "| only"):
                        results.append(item)
                value = results
            else:
                _, callee, args = stage
                fn = self.eval(callee, scope)
                value = self.call_function(fn, [value] + [self.eval(a, scope) for a in args],
                                           callee, callee.name)
        return value

    def eval_Await(self, node, scope):
        owner = scope.find(node.name)
        task = owner.vars[node.name] if owner is not None else None
        if not isinstance(task, TaskValue):
            self.fail(node, f"'{node.name}' is not a task, so there's nothing to await.",
                      hint=f"Start one first with:  task {node.name} ... .")
        self.wait_for(task)
        task.awaited = True
        if task.error is not None:
            raise task.error
        return task.result

    def eval_Call(self, node, scope):
        callee = node.callee
        if isinstance(callee, N.Name) and scope.find(callee.name) is None \
                and callee.name not in FRIENDLY_RENAMES:
            make = f"make it first with:  fn {callee.name} ...  (and end the block with a '.' line)"
            guess = did_you_mean(callee.name, scope.all_names())
            hint = f"{guess} If it's your own function, {make}" if guess else make[0].upper() + make[1:]
            self.fail(callee, f"I don't know a function called '{callee.name}'.", hint)
        fn = self.eval(callee, scope)
        args = [self.eval(a, scope) for a in node.args]
        name = node.callee.name if isinstance(node.callee, N.Name) else "this function"
        return self.call_function(fn, args, node, name)

    def call_function(self, fn, args, node, name):
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
            self.fail(node, f"'{name}' is {type_name(fn)}, not a function, so it can't be called with ( ).",
                      hint="To get an item from a list, use [ ], like: my_list[1]")

        if len(args) != len(fn.params):
            params = ", ".join(fn.params)
            self.fail(node, f"{fn.name}() needs {len(fn.params)} value{'s' if len(fn.params) != 1 else ''}"
                            f" ({params}) but got {len(args)}.")

        if self.depth >= MAX_CALL_DEPTH:
            self.fail(node, f"Too many functions calling each other (more than {MAX_CALL_DEPTH} deep).",
                      hint=f"Does '{fn.name}' keep calling itself forever? Make sure it can 'ret' without calling itself.")
        local = Scope(fn.closure)
        local.vars.update(zip(fn.params, args))
        if self.interrupted:
            raise KeyboardInterrupt
        self.depth += 1
        try:
            self.exec_block(fn.body, local)
        except _Return as ret:
            return ret.value
        except SimpleTalkError as err:
            if err.source is None and fn.source is not None and fn.source is not self.source:
                err.source, err.filename = fn.source, fn.filename   # it happened in another file
            raise
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
