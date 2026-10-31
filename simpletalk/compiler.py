"""The fast engine: turn the syntax tree into ready-to-run Python functions.

The plain interpreter looks at every node each time it runs ("which kind of
node is this? which method handles it?"). That lookup is most of the cost of
a tight loop. Here each node is turned, once, into a small Python function
(a closure) that already knows what to do, with fast paths for the common
cases: whole-number maths, comparisons, variables, loops and calls.

Anything unusual takes the slow path through the interpreter's own methods,
so behaviour and error messages are exactly the same as before.
"""

from . import nodes as N
from .errors import SimpleTalkError
from .values import equal, show


def compile_block(interp, body):
    """Return run(scope) for a list of statements."""
    steps = [compile_stmt(interp, node) for node in body]
    if not steps:
        return lambda scope: None
    if len(steps) == 1:
        return steps[0]

    def run(scope):
        for step in steps:
            step(scope)
    return run


# ------------------------------------------------------------------ statements
def compile_stmt(interp, node):
    core = _stmt_core(interp, node)
    line, column = node.line, node.column

    def step(scope):
        if interp.interrupted:
            raise KeyboardInterrupt
        if interp.trace is not None:
            interp.trace(line)
        try:
            core(scope)
        except SimpleTalkError as err:
            if err.line is None:
                err.line, err.column = line, column
            raise
    return step


def _stmt_core(interp, node):
    kind = type(node)
    from .interpreter import _Return, _Skip, _Stop

    if kind is N.Say:
        values = [compile_expr(interp, v) for v in node.values]

        def say(scope):
            interp.output(" ".join([show(v(scope)) for v in values]))
        return say

    if kind is N.Set and isinstance(node.target, N.Name):
        name = node.target.name
        value = compile_expr(interp, node.value)
        assign = interp.assign

        def let(scope):
            assign(name, value(scope), scope, node)
        return let

    if kind is N.Change:
        name = node.name
        amount = compile_expr(interp, node.amount)
        builtins_scope = interp.builtins

        def up(scope):
            owner = scope
            while owner is not None and name not in owner.vars:
                owner = owner.parent
            if owner is None or owner is builtins_scope:
                return interp.exec_Change(node, scope)      # gives the friendly error
            current = owner.vars[name]
            add = amount(scope)
            if type(current) is int and type(add) is int and name not in interp.watched:
                owner.vars[name] = current + add
            else:
                interp.change_value(node, owner, current, add)
        return up

    if kind is N.If:
        branches = [(compile_expr(interp, c), c, compile_block(interp, b)) for c, b in node.branches]
        otherwise = compile_block(interp, node.else_body) if node.else_body is not None else None
        need_bool = interp.need_bool

        def when(scope):
            for cond, cond_node, body in branches:
                v = cond(scope)
                if v is True or (v is not False and need_bool(cond_node, v, "when")):
                    body(scope)
                    return
            if otherwise is not None:
                otherwise(scope)
        return when

    if kind is N.RepeatTimes:
        count = compile_expr(interp, node.count)
        body = compile_block(interp, node.body)

        def repeat(scope):
            n = count(scope)
            if type(n) is not int:
                n = interp.check_count(node, n)
            elif n < 0:
                interp.check_count(node, n)
            for _ in range(n):
                if interp.interrupted:
                    raise KeyboardInterrupt
                try:
                    body(scope)
                except _Skip:
                    pass
                except _Stop:
                    break
        return repeat

    if kind is N.RepeatWhile:
        cond = compile_expr(interp, node.condition) if node.condition is not None else None
        cond_node = node.condition
        body = compile_block(interp, node.body)
        need_bool = interp.need_bool

        def loop_while(scope):
            while True:
                if cond is not None:
                    v = cond(scope)
                    if v is not True and (v is False or not need_bool(cond_node, v, "loop while")):
                        break
                if interp.interrupted:
                    raise KeyboardInterrupt
                try:
                    body(scope)
                except _Skip:
                    pass
                except _Stop:
                    break
        return loop_while

    if kind is N.ForEach:
        var = node.var
        body = compile_block(interp, node.body)
        it = node.iterable
        is_range = isinstance(it, N.Binary) and it.op == ".."
        items_of = None if is_range else compile_expr(interp, it)

        def loop_each(scope):
            if is_range:
                start, end = interp.range_ends(it, scope)
                if type(start) is int and type(end) is int:
                    items = range(start, end + 1) if end >= start else range(start, end - 1, -1)
                else:
                    items = interp.range_iter(it, scope)
            else:
                items = items_of(scope)
                if isinstance(items, (str, list, dict)):
                    items = list(items)          # loop over a copy (a map gives its keys)
                else:
                    interp.bad_loop_items(node, items)
            vars_ = scope.vars
            watched = interp.watched
            for item in items:
                if var in watched:
                    old = vars_.get(var, interp.MISSING)
                    vars_[var] = item
                    interp.report(var, old, item, node)
                else:
                    vars_[var] = item
                if interp.interrupted:
                    raise KeyboardInterrupt
                try:
                    body(scope)
                except _Skip:
                    pass
                except _Stop:
                    break
        return loop_each

    if kind is N.ExprStatement:
        expr = compile_expr(interp, node.expr)
        return expr

    if kind is N.Return:
        value = compile_expr(interp, node.value) if node.value is not None else None

        def ret(scope):
            raise _Return(value(scope) if value is not None else None)
        return ret

    if kind is N.Stop:
        def stop(scope):
            raise _Stop()
        return stop

    if kind is N.Skip:
        def skip(scope):
            raise _Skip()
        return skip

    # Everything else is rare in tight loops: use the interpreter's own method.
    method = getattr(interp, "exec_" + kind.__name__)
    return lambda scope: method(node, scope)


# ------------------------------------------------------------------ expressions
def compile_expr(interp, node):
    fn = _expr(interp, node)
    return fn


def _expr(interp, node):
    kind = type(node)

    if kind is N.Literal:
        value = node.value
        return lambda scope: value

    if kind is N.Name:
        name = node.name

        def get(scope):
            s = scope
            while s is not None:
                v = s.vars
                if name in v:
                    return v[name]
                s = s.parent
            return interp.eval_Name(node, scope)          # gives the friendly error
        return get

    if kind is N.Text:
        parts = [p if isinstance(p, str) else compile_expr(interp, p) for p in node.parts]

        def text(scope):
            return "".join([p if p.__class__ is str else show(p(scope)) for p in parts])
        return text

    if kind is N.ListLiteral:
        items = [compile_expr(interp, i) for i in node.items]
        return lambda scope: [i(scope) for i in items]

    if kind is N.MapLiteral:
        items = [(k, compile_expr(interp, v)) for k, v in node.items]
        return lambda scope: {k: v(scope) for k, v in items}

    if kind is N.Unary:
        operand = compile_expr(interp, node.operand)
        if node.op == "not":
            need_bool = interp.need_bool
            child = node.operand

            def negate(scope):
                v = operand(scope)
                if v is True:
                    return False
                if v is False:
                    return True
                return not need_bool(child, v, "not")
            return negate

        def minus(scope):
            v = operand(scope)
            if type(v) is int or type(v) is float:
                return -v
            return interp.eval_Unary(node, scope)             # gives the friendly error
        return minus

    if kind is N.Binary:
        return _binary(interp, node)

    if kind is N.Call:
        return _call(interp, node)

    if kind is N.Index:
        target = compile_expr(interp, node.target)
        index = compile_expr(interp, node.index)
        index_value = interp.index_value

        def get_item(scope):
            c = target(scope)
            i = index(scope)
            if type(c) is list and type(i) is int and 0 < i <= len(c):
                return c[i - 1]
            return index_value(node, c, i)
        return get_item

    if kind is N.Field:
        target = compile_expr(interp, node.target)
        name = node.name
        field_value = interp.field_value

        def get_field(scope):
            c = target(scope)
            if type(c) is dict and name in c:
                return c[name]
            return field_value(node, c)
        return get_field

    # Pipe, Lambda, Await and anything new: the interpreter's own method.
    method = getattr(interp, "eval_" + kind.__name__)
    return lambda scope: method(node, scope)


def _binary(interp, node):
    op = node.op
    if op == "..":
        return lambda scope: interp.eval_range(node, scope)

    left = compile_expr(interp, node.left)
    right = compile_expr(interp, node.right)
    need_bool = interp.need_bool

    if op == "and":
        def both(scope):
            a = left(scope)
            if a is not True and (a is False or not need_bool(node.left, a, "and")):
                return False
            b = right(scope)
            return b if b is True or b is False else need_bool(node.right, b, "and")
        return both

    if op == "or":
        def either(scope):
            a = left(scope)
            if a is True or (a is not False and need_bool(node.left, a, "or")):
                return True
            b = right(scope)
            return b if b is True or b is False else need_bool(node.right, b, "or")
        return either

    binop = interp.binop

    # Fast paths only for plain whole numbers; everything else (decimals,
    # text, lists, errors) goes through binop, the single source of truth.
    if op == "+":
        def add(scope):
            a = left(scope); b = right(scope)
            if type(a) is int and type(b) is int:
                return a + b
            return binop(node, op, a, b)
        return add
    if op == "-":
        def sub(scope):
            a = left(scope); b = right(scope)
            if type(a) is int and type(b) is int:
                return a - b
            return binop(node, op, a, b)
        return sub
    if op == "*":
        def mul(scope):
            a = left(scope); b = right(scope)
            if type(a) is int and type(b) is int:
                return a * b
            return binop(node, op, a, b)
        return mul
    if op == "mod":
        def mod(scope):
            a = left(scope); b = right(scope)
            if type(a) is int and type(b) is int and b != 0:
                return a % b
            return binop(node, op, a, b)
        return mod
    if op == "=":
        def eq(scope):
            a = left(scope); b = right(scope)
            if type(a) is type(b) and (type(a) is int or type(a) is str):
                return a == b
            return equal(a, b)
        return eq
    if op == "!=":
        def ne(scope):
            a = left(scope); b = right(scope)
            if type(a) is type(b) and (type(a) is int or type(a) is str):
                return a != b
            return not equal(a, b)
        return ne
    if op == "<":
        def lt(scope):
            a = left(scope); b = right(scope)
            if type(a) is int and type(b) is int:
                return a < b
            return binop(node, op, a, b)
        return lt
    if op == ">":
        def gt(scope):
            a = left(scope); b = right(scope)
            if type(a) is int and type(b) is int:
                return a > b
            return binop(node, op, a, b)
        return gt
    if op == "<=":
        def le(scope):
            a = left(scope); b = right(scope)
            if type(a) is int and type(b) is int:
                return a <= b
            return binop(node, op, a, b)
        return le
    if op == ">=":
        def ge(scope):
            a = left(scope); b = right(scope)
            if type(a) is int and type(b) is int:
                return a >= b
            return binop(node, op, a, b)
        return ge

    def other(scope):                                   # "/", "has"
        return binop(node, op, left(scope), right(scope))
    return other


def _call(interp, node):
    callee = node.callee
    args = [compile_expr(interp, a) for a in node.args]
    call_function = interp.call_function

    if not isinstance(callee, N.Name):
        get_fn = compile_expr(interp, callee)

        def call_value(scope):
            fn = get_fn(scope)
            return call_function(fn, [a(scope) for a in args], node, "this function")
        return call_value

    name = callee.name

    def call(scope):
        s = scope
        while s is not None:
            v = s.vars
            if name in v:
                fn = v[name]
                break
            s = s.parent
        else:
            return interp.eval_Call(node, scope)             # gives the friendly error
        return call_function(fn, [a(scope) for a in args], node, name)
    return call
