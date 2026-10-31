"""The building blocks (AST nodes) a SimpleTalk program is turned into.

Every node remembers its line number so errors can point at the right place.
"""

from dataclasses import dataclass, field


@dataclass
class Node:
    line: int = field(default=0, kw_only=True)
    column: int = field(default=0, kw_only=True)


# ---------------- expressions (things that have a value) ----------------
@dataclass
class Literal(Node):
    value: object


@dataclass
class Text(Node):
    parts: list            # str or expression nodes


@dataclass
class ListLiteral(Node):
    items: list


@dataclass
class Name(Node):
    name: str


@dataclass
class Unary(Node):
    op: str
    operand: Node


@dataclass
class Binary(Node):
    op: str
    left: Node
    right: Node


@dataclass
class MapLiteral(Node):
    items: list            # list of (key text, value node)


@dataclass
class Field(Node):
    target: Node
    name: str              # me.name


@dataclass
class Pipe(Node):
    value: Node
    stages: list           # ("only", expr) | ("each", expr) | ("call", callee, args)


@dataclass
class Lambda(Node):
    params: list
    body: Node             # fn a b -> a + b


@dataclass
class Await(Node):
    name: str


@dataclass
class Call(Node):
    callee: Node
    args: list


@dataclass
class Index(Node):
    target: Node
    index: Node


# ---------------- statements (things that do something) ----------------
@dataclass
class Say(Node):
    values: list


@dataclass
class Ask(Node):
    prompt: Node | None
    target: str
    kind: str | None = None     # None (any answer), "num" or "yes"


@dataclass
class Set(Node):
    target: Node           # Name or Index
    value: Node


@dataclass
class Change(Node):
    name: str
    amount: Node


@dataclass
class Add(Node):
    value: Node
    target: Node


@dataclass
class Remove(Node):
    value: Node
    target: Node


@dataclass
class If(Node):
    branches: list         # list of (condition, body)
    else_body: list | None


@dataclass
class RepeatTimes(Node):
    count: Node
    body: list


@dataclass
class RepeatWhile(Node):
    condition: Node | None   # None means forever
    body: list


@dataclass
class ForEach(Node):
    var: str
    iterable: Node
    body: list



@dataclass
class Define(Node):
    name: str
    params: list
    body: list


@dataclass
class Return(Node):
    value: Node | None


@dataclass
class Stop(Node):
    pass


@dataclass
class Skip(Node):
    pass


@dataclass
class Watch(Node):
    names: list


@dataclass
class Test(Node):
    expr: Node
    text: str                   # the check as written, shown when it fails


@dataclass
class Try(Node):
    body: list
    err_name: str | None
    handler: list


@dataclass
class Oops(Node):
    message: Node


@dataclass
class Use(Node):
    path: Node


@dataclass
class Pick(Node):
    value: Node
    cases: list            # list of (patterns, body)
    else_body: list | None


@dataclass
class Keep(Node):
    name: str
    default: Node


@dataclass
class Task(Node):
    name: str
    body: list


@dataclass
class ExprStatement(Node):
    expr: Node
