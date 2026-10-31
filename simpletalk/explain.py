"""`simpletalk --explain file.simp`: read a program back in plain English.

Useful for learning ("what does this line do?") and for checking that the
program says what you meant before you run it.
"""

from . import nodes as N
from .values import show

OPS = {
    "+": "plus", "-": "minus", "*": "times", "/": "divided by", "mod": "mod",
    "=": "equals", "!=": "is not equal to", "<": "is less than", ">": "is greater than",
    "<=": "is at most", ">=": "is at least", "has": "contains",
    "and": "and", "or": "or",
}

BUILTIN_WORDS = {
    "len": "the length of {0}",
    "num": "{0} as a number",
    "isnum": "whether {0} is a number",
    "txt": "{0} as text",
    "type": "the type of {0}",
    "round": "{0} rounded",
    "abs": "the size of {0} without its sign",
    "sqrt": "the square root of {0}",
    "pow": "{0} to the power of {1}",
    "rand": "a random whole number from {0} to {1}",
    "min": "the smallest of {all}",
    "max": "the largest of {all}",
    "sum": "the total of {0}",
    "upper": "{0} in capital letters",
    "lower": "{0} in small letters",
    "trim": "{0} without spaces at the ends",
    "swap": "{0} with {1} replaced by {2}",
    "split": "{0} split into a list",
    "join": "the items of {0} joined into one text",
    "sort": "{0} sorted",
    "rev": "{0} reversed",
    "copy": "a copy of {0}",
    "wait": "a pause of {0} seconds",
}


def words(node):
    """Describe an expression in plain words."""
    if isinstance(node, N.Literal):
        if isinstance(node.value, str):
            return f'"{node.value}"'
        return show(node.value)
    if isinstance(node, N.Text):
        inner = "".join(p if isinstance(p, str) else "{" + code(p) + "}" for p in node.parts)
        return f'"{inner}"'
    if isinstance(node, N.Name):
        return node.name
    if isinstance(node, N.ListLiteral):
        if not node.items:
            return "an empty list"
        return "the list [" + ", ".join(code(i) for i in node.items) + "]"
    if isinstance(node, N.Unary):
        if node.op == "not":
            return f"not ({words(node.operand)})"
        if isinstance(node.operand, N.Literal) and not isinstance(node.operand.value, (str, bool)):
            return "-" + words(node.operand)
        return f"minus {words(node.operand)}"
    if isinstance(node, N.Binary):
        if node.op == "..":
            return f"the numbers from {words(node.left)} to {words(node.right)}"
        return f"{words(node.left)} {OPS[node.op]} {words(node.right)}"
    if isinstance(node, N.Index):
        index = node.index
        if isinstance(index, N.Literal) and index.value == -1:
            return f"the last item of {words(node.target)}"
        if isinstance(index, N.Literal) and index.value == 1:
            return f"the first item of {words(node.target)}"
        return f"item {words(index)} of {words(node.target)}"
    if isinstance(node, N.Call):
        args = [words(a) for a in node.args]
        if isinstance(node.callee, N.Name):
            pattern = BUILTIN_WORDS.get(node.callee.name)
            if pattern and (args or "{all}" not in pattern):
                try:
                    return pattern.format(*args, all=", ".join(args))
                except IndexError:
                    pass
            if not args:
                return f"the result of {node.callee.name}"
            return f"the result of {node.callee.name} with {', '.join(args)}"
        return "the result of a function call"
    return "a value"


def code(node):
    """Turn an expression back into SimpleTalk code (used inside {braces})."""
    if isinstance(node, N.Literal):
        return f'"{node.value}"' if isinstance(node.value, str) else show(node.value)
    if isinstance(node, N.Name):
        return node.name
    if isinstance(node, N.Binary):
        return f"{code(node.left)} {node.op} {code(node.right)}"
    if isinstance(node, N.Unary):
        return f"not {code(node.operand)}" if node.op == "not" else f"-{code(node.operand)}"
    if isinstance(node, N.Call):
        return f"{code(node.callee)}({', '.join(code(a) for a in node.args)})"
    if isinstance(node, N.Index):
        return f"{code(node.target)}[{code(node.index)}]"
    if isinstance(node, N.ListLiteral):
        return "[" + ", ".join(code(i) for i in node.items) + "]"
    if isinstance(node, N.Text):
        return '"' + "".join(p if isinstance(p, str) else "{" + code(p) + "}" for p in node.parts) + '"'
    return "..."


def sentence(node):
    """Describe one statement. Returns (text, [(label, body), ...])."""
    if isinstance(node, N.Say):
        if not node.values:
            return "Show an empty line.", []
        return "Show " + ", then ".join(words(v) for v in node.values) + ".", []
    if isinstance(node, N.Set):
        if isinstance(node.target, N.Name):
            return f"Store {words(node.value)} in {node.target.name}.", []
        return f"Change {words(node.target)} to {words(node.value)}.", []
    if isinstance(node, N.Change):
        amount = node.amount
        if isinstance(amount, N.Unary) and amount.op == "-":
            return f"Take {words(amount.operand)} away from {node.name}.", []
        if isinstance(amount, N.Literal) and amount.value == 1:
            return f"Add 1 to {node.name}.", []
        return f"Add {words(amount)} to {node.name}.", []
    if isinstance(node, N.Ask):
        question = f"the question {words(node.prompt)}" if node.prompt else "for an answer"
        rule = {"num": " (asking again until a number is typed)",
                "yes": " (asking again until yes or no is typed; stored as true or false)"}.get(node.kind, "")
        return f"Ask {question} and store the answer in {node.target}{rule}.", []
    if isinstance(node, N.Add):
        return f"Put {words(node.value)} at the end of the list {words(node.target)}.", []
    if isinstance(node, N.Remove):
        return f"Delete the first {words(node.value)} from the list {words(node.target)}.", []
    if isinstance(node, N.If):
        parts = []
        for i, (cond, body) in enumerate(node.branches):
            label = f"If {words(cond)}:" if i == 0 else f"Otherwise, if {words(cond)}:"
            parts.append((label, body))
        if node.else_body is not None:
            parts.append(("Otherwise:", node.else_body))
        first_label, first_body = parts[0]
        return first_label, [(None, first_body)] + parts[1:]
    if isinstance(node, N.RepeatTimes):
        return f"Do this {words(node.count)} times:", [(None, node.body)]
    if isinstance(node, N.RepeatWhile):
        if node.condition is None:
            return "Do this again and again, until 'stop':", [(None, node.body)]
        return f"While {words(node.condition)}, do this:", [(None, node.body)]
    if isinstance(node, N.ForEach):
        it = node.iterable
        if isinstance(it, N.Binary) and it.op == "..":
            return (f"Count {node.var} from {words(it.left)} to {words(it.right)}, and each time:",
                    [(None, node.body)])
        return f"For each {node.var} in {words(it)}:", [(None, node.body)]
    if isinstance(node, N.Define):
        if node.params:
            takes = "takes " + " and ".join(node.params)
        else:
            takes = "takes no inputs"
        return f"Make a function called {node.name} that {takes}. It will:", [(None, node.body)]
    if isinstance(node, N.Return):
        if node.value is None:
            return "Leave the function.", []
        return f"Give back {words(node.value)}.", []
    if isinstance(node, N.Stop):
        return "Leave the loop now.", []
    if isinstance(node, N.Skip):
        return "Skip to the next round of the loop.", []
    if isinstance(node, N.Watch):
        return "From now on, report every change to " + " and ".join(node.names) + ".", []
    if isinstance(node, N.Test):
        return f"Check that {words(node.expr)}; stop with a message if it isn't true.", []
    if isinstance(node, N.ExprStatement):
        expr = node.expr
        if isinstance(expr, N.Call) and isinstance(expr.callee, N.Name):
            args = [words(a) for a in expr.args]
            if expr.callee.name == "wait" and args:
                return f"Wait {args[0]} seconds.", []
            return f"Run {expr.callee.name}" + (f" with {', '.join(args)}." if args else "."), []
        return f"Work out {words(expr)}.", []
    return "(something SimpleTalk can run)", []


def explain(program):
    """Return the plain-English description of a parsed program, as text."""
    out = []

    def walk(body, depth):
        for node in body:
            text, children = sentence(node)
            if text.endswith('".'):
                text = text[:-1]          # Show "Hi". -> Show "Hi"
            out.append(f"{node.line:>4}  {'    ' * depth}{text}")
            for label, child in children:
                if label is not None:
                    out.append(f"{'':>4}  {'    ' * depth}{label}")
                walk(child, depth + 1)

    walk(program, 0)
    return "\n".join(out)
