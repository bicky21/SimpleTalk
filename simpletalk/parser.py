"""Step 2: turn the list of tokens into a tree of nodes (the program's structure).

SimpleTalk 2.0 grammar, in one screen:

    let NAME VALUE            let NAME[POS] VALUE
    up NAME [AMOUNT]          out [VALUE, VALUE, ...]
    in NAME [num|yes] [PROMPT]                      add LIST VALUE   del LIST VALUE
    when COND ... (else when COND ...)* (else ...)? .
    loop ... .                loop N ... .          loop while COND ... .
    loop NAME LIST_OR_RANGE ... .
    fn NAME PARAM PARAM ... .                       ret [VALUE]
    stop                      skip                  NAME(ARGS)
    watch NAME NAME ...       test CHECK
    try ... fail [NAME] ... .                       oops MESSAGE
    pick VALUE  is PATTERN, ... ...  else ... .     use "file"
    keep NAME DEFAULT         task NAME ... .       await NAME

Values: {name: "Bicky"}  me.name  fn a b -> a + b  list | only it > 1 | each it * 2

A block is closed by a line holding just a dot.
Rule for calls and positions: no space before ( or [  ->  area(3, 4)  list[1]
"""

from . import nodes as N
from .errors import SyntaxProblem
from .lexer import TextPart, TextValue, tokenize

COMPARE_OPS = {"=", "!=", "<", ">", "<=", ">="}

# Words people bring from other languages (or SimpleTalk 1.0) -> 2.0 word.
OLD_WORDS = {
    "say": "out", "print": "out", "echo": "out", "puts": "out", "console": "out",
    "set": "let", "var": "let", "const": "let",
    "ask": "in", "input": "in",
    "change": "up",
    "if": "when", "elif": "else when", "then": None,
    "repeat": "loop", "for": "loop", "forever": "loop", "do": "loop",
    "define": "fn", "def": "fn", "function": "fn", "func": "fn",
    "return": "ret", "break": "stop", "continue": "skip",
    "remove": "del", "append": "add", "push": "add",
    "end": ".", "endif": ".", "done": ".",
    "import": "use", "include": "use", "require": "use",
    "match": "pick", "switch": "pick", "case": "is",
    "raise": "oops", "throw": "oops", "catch": "fail", "except": "fail",
    "async": "task", "lambda": "fn",
}


class Parser:
    def __init__(self, tokens, source=None):
        self.tokens = tokens
        self.lines = source.replace("\r\n", "\n").replace("\r", "\n").split("\n") if source else None
        self.i = 0
        self.loop_depth = 0
        self.func_depth = 0

    # -- helpers -------------------------------------------------------
    @property
    def tok(self):
        return self.tokens[self.i]

    def peek(self, ahead=1):
        j = min(self.i + ahead, len(self.tokens) - 1)
        return self.tokens[j]

    def at(self, kind, value=None, tok=None):
        tok = tok or self.tok
        return tok.kind == kind and (value is None or tok.value == value)

    def at_kw(self, *words):
        return self.tok.kind == "KEYWORD" and self.tok.value in words

    def at_line_end(self):
        return self.at("NEWLINE") or self.at("EOF")

    def next(self):
        tok = self.tok
        if tok.kind != "EOF":
            self.i += 1
        return tok

    def describe(self, tok):
        if tok.kind == "NEWLINE":
            return "the end of the line"
        if tok.kind == "EOF":
            return "the end of the program"
        if tok.kind == "TEXT":
            return "some text"
        return f"'{tok.value}'"

    def fail(self, message, tok=None, hint=None):
        tok = tok or self.tok
        raise SyntaxProblem(message, tok.line, tok.column, hint)

    def expect_sym(self, sym, hint=None):
        if not self.at("SYMBOL", sym):
            self.fail(f"I expected '{sym}' here, but found {self.describe(self.tok)}.", hint=hint)
        return self.next()

    def expect_name(self, what="a name"):
        if self.tok.kind == "KEYWORD":
            self.fail(f"'{self.tok.value}' is a SimpleTalk word, so it can't be used as {what}.",
                      hint=f"Pick a different name, like my_{self.tok.value}")
        if self.tok.kind != "NAME":
            self.fail(f"I expected {what} here, but found {self.describe(self.tok)}.")
        return self.next()

    def end_of_line(self):
        if self.at("NEWLINE"):
            self.next()
            return
        if self.at("EOF"):
            return
        hint = "Each instruction goes on its own line."
        prev = self.tokens[self.i - 1] if self.i else None
        if self.at("SYMBOL", ":") and self.peek().kind in ("NEWLINE", "EOF"):
            self.fail("SimpleTalk doesn't put ':' at the end of a line.",
                      hint="Just remove it. The block ends with a line holding a dot ( . )")
        if self.at("SYMBOL") and self.tok.value in "([" and self.tok.spaced and prev is not None \
                and prev.kind in ("NAME", "SYMBOL", "TEXT") and prev.value not in ("(", "[", ","):
            hint = f"Remove the space before '{self.tok.value}', like: name{self.tok.value}...{')' if self.tok.value == '(' else ']'}"
        self.fail(f"I didn't expect {self.describe(self.tok)} here.", hint=hint)

    def skip_newlines(self):
        while self.at("NEWLINE"):
            self.next()

    def at_field(self):
        """`me.name`: a dot touching a name on both sides (a lone '.' closes a block)."""
        nxt = self.peek()
        return (self.at("SYMBOL", ".") and not self.tok.spaced
                and nxt.kind in ("NAME", "KEYWORD") and not nxt.spaced)

    def starts_value(self, tok, after):
        """Can `tok` begin a new value? Used to tell `loop i 1..5` from `loop n`."""
        if tok.kind in ("NUMBER", "TEXT", "NAME"):
            return True
        if tok.kind == "KEYWORD" and tok.value in ("true", "false", "none", "not", "fn", "await"):
            return True
        if tok.kind == "SYMBOL" and tok.value in ("(", "[", "{"):
            return tok.spaced
        if tok.kind == "SYMBOL" and tok.value == "-":
            return tok.spaced and not after.spaced      # `-3` yes, `- 3` no
        return False

    # -- program and blocks ---------------------------------------------
    def parse_program(self):
        try:
            return self._parse_program()
        except RecursionError:
            raise SyntaxProblem("This code is nested too deeply for me to read.", None, None,
                                "Try splitting it into smaller pieces.")

    def _parse_program(self):
        body = []
        self.skip_newlines()
        while not self.at("EOF"):
            if self.at("SYMBOL", "."):
                self.fail("This '.' has no block to close.",
                          hint="Remove it, or check the block above was opened correctly.")
            if self.at_kw("else"):
                self.fail("This 'else' is not inside a 'when'.")
            body.append(self.statement())
            self.skip_newlines()
        return body

    def at_block_end(self):
        return self.at("SYMBOL", ".")

    def block(self, opener, open_tok, stop_at_else=False, stop_words=()):
        """Read statements until the closing '.' (and 'else' / other stop words)."""
        body = []
        self.skip_newlines()
        while True:
            if stop_words and self.at_kw(*stop_words):
                return body
            if self.at("EOF"):
                raise SyntaxProblem(
                    f"The '{opener}' that starts on line {open_tok.line} was never closed.",
                    open_tok.line, open_tok.column,
                    "Add a line with just a dot ( . ) after the block.",
                    incomplete=True)
            if self.at_block_end():
                return body
            if self.at_kw("else"):
                if stop_at_else:
                    return body
                self.fail("This 'else' is not inside a 'when'.")
            body.append(self.statement())
            self.skip_newlines()

    def close_block(self):
        self.expect_sym(".")
        if not self.at_line_end():
            self.fail("The closing '.' must be alone on its line.")
        self.end_of_line()

    # -- statements ------------------------------------------------------
    def statement(self):
        tok = self.tok
        if tok.kind == "KEYWORD":
            handler = getattr(self, f"stmt_{tok.value}", None)
            if handler:
                return handler()
        if tok.kind == "NAME":
            self.check_old_word(tok)
        return self.expression_statement()

    def check_old_word(self, tok):
        """Friendly hint when someone writes `say`, `print`, `if`, `set x to` ..."""
        word = tok.value
        nxt = self.peek()
        if word not in OLD_WORDS:
            if nxt.kind == "SYMBOL" and nxt.value == "=":
                self.fail(f"To store a value, write: let {word} ...", tok,
                          hint=f"SimpleTalk uses 'let name value', like: let {word} 5")
            return
        # `print(x)` with a real function called print is fine.
        if nxt.kind == "SYMBOL" and nxt.value == "(" and not nxt.spaced:
            return
        new = OLD_WORDS[word]
        if new is None:
            self.fail(f"'{word}' isn't needed in SimpleTalk.", tok, hint="Just leave it out.")
        if new == ".":
            self.fail(f"Blocks end with a line holding just a dot, not '{word}'.", tok,
                      hint="Replace this line with:  .")
        self.fail(f"SimpleTalk doesn't use '{word}'. The word for that is '{new}'.", tok,
                  hint=f"Write '{new}' instead of '{word}'. All words are listed in docs/LANGUAGE.md.")

    def target(self, what):
        """A variable name, optionally with a position: score, list[2], grid[1][3]."""
        tok = self.tok
        name = self.expect_name(what)
        node = N.Name(name.value, line=name.line, column=name.column)
        while True:
            if self.at("SYMBOL", "[") and not self.tok.spaced:
                br = self.next()
                index = self.expression()
                self.expect_sym("]")
                node = N.Index(node, index, line=br.line, column=br.column)
            elif self.at_field():
                dot = self.next()
                node = N.Field(node, self.next().value, line=dot.line, column=dot.column)
            else:
                return node

    def stmt_let(self):
        tok = self.next()
        target = self.target("a variable name")
        if self.at("SYMBOL", "="):
            self.fail("'let' doesn't need '='.", hint=f"Write it like: let {self.describe_target(target)} 10")
        if self.at_line_end():
            self.fail("'let' needs a value to store.", hint="Write it like: let score 10")
        value = self.expression()
        self.end_of_line()
        return N.Set(target, value, line=tok.line, column=tok.column)

    @staticmethod
    def describe_target(node):
        return node.name if isinstance(node, N.Name) else "name"

    def stmt_up(self):
        tok = self.next()
        name = self.expect_name("a variable name")
        if self.at_line_end():
            amount = N.Literal(1, line=tok.line, column=tok.column)
        else:
            amount = self.expression()
        self.end_of_line()
        return N.Change(name.value, amount, line=tok.line, column=tok.column)

    def stmt_out(self):
        tok = self.next()
        values = []
        if not self.at_line_end():
            values.append(self.expression())
            while self.at("SYMBOL", ","):
                self.next()
                values.append(self.expression())
        self.end_of_line()
        return N.Say(values, line=tok.line, column=tok.column)

    def stmt_in(self):
        tok = self.next()
        name = self.expect_name("a variable name to store the answer in")
        kind = None
        # `in age num "Age?"` keeps asking until a number is typed,
        # `in ok yes "Sure?"` until yes or no is typed.
        if self.at("NAME") and self.tok.value in ("num", "yes"):
            kind = self.next().value
        prompt = None
        if not self.at_line_end():
            prompt = self.expression()
        self.end_of_line()
        return N.Ask(prompt, name.value, kind, line=tok.line, column=tok.column)

    def stmt_watch(self):
        tok = self.next()
        if self.at_line_end():
            self.fail("'watch' needs the name of a variable.", hint="Write it like: watch score")
        names = []
        while not self.at_line_end():
            if self.at("SYMBOL", ","):
                self.next()
                continue
            names.append(self.expect_name("a variable name").value)
        self.end_of_line()
        return N.Watch(names, line=tok.line, column=tok.column)

    def stmt_test(self):
        tok = self.next()
        if self.at_line_end():
            self.fail("'test' needs something to check.", hint="Write it like: test square(3) = 9")
        start = self.tok
        expr = self.expression()
        text = "this check"
        if self.lines and 1 <= start.line <= len(self.lines):
            text = self.lines[start.line - 1][start.column - 1:].split(";;")[0].strip()
        self.end_of_line()
        return N.Test(expr, text, line=tok.line, column=tok.column)

    def list_change(self, cls, word):
        tok = self.next()
        target = self.target("a list name")
        if self.at_line_end():
            self.fail(f"'{word}' needs a value.", hint=f'Write it like: {word} fruits "kiwi"')
        value = self.expression()
        self.end_of_line()
        return cls(value, target, line=tok.line, column=tok.column)

    def stmt_add(self):
        return self.list_change(N.Add, "add")

    def stmt_del(self):
        return self.list_change(N.Remove, "del")

    def condition_line(self):
        if self.at_line_end():
            self.fail("'when' needs something to check.", hint="Write it like: when age > 18")
        cond = self.expression()
        if self.at("SYMBOL", ":"):
            self.end_of_line()                 # gives the "no ':' needed" hint
        if not self.at_line_end():
            self.fail(f"I didn't expect {self.describe(self.tok)} here.",
                      hint="Put the code that should run on the next line, and end the block with a '.' line.")
        return cond

    def stmt_when(self):
        tok = self.next()
        branches = [(self.condition_line(), self.block("when", tok, stop_at_else=True))]
        else_body = None
        while self.at_kw("else"):
            else_tok = self.next()
            if self.at_kw("when"):
                self.next()
                branches.append((self.condition_line(), self.block("when", tok, stop_at_else=True)))
                continue
            if not self.at_line_end():
                self.fail("Put the code for 'else' on the next line.", else_tok,
                          hint="For another check, write: else when ...")
            else_body = self.block("when", tok, stop_at_else=True)
            if self.at_kw("else"):
                self.fail("A 'when' can only have one plain 'else', and it must come last.")
            break
        self.close_block()
        return N.If(branches, else_body, line=tok.line, column=tok.column)

    def loop_body(self, open_tok):
        self.loop_depth += 1
        try:
            body = self.block("loop", open_tok)
        finally:
            self.loop_depth -= 1
        self.close_block()
        return body

    def stmt_loop(self):
        tok = self.next()
        line, col = tok.line, tok.column
        if self.at_line_end():                                   # loop  (forever)
            self.end_of_line()
            return N.RepeatWhile(None, self.loop_body(tok), line=line, column=col)
        if self.at_kw("while"):                                  # loop while x < 10
            self.next()
            if self.at_line_end():
                self.fail("'loop while' needs something to check.", hint="Write it like: loop while x < 10")
            cond = self.expression()
            self.end_of_line()
            return N.RepeatWhile(cond, self.loop_body(tok), line=line, column=col)
        if self.at("NAME") and self.starts_value(self.peek(), self.peek(2)):
            var = self.next().value                              # loop i 1..5 / loop f fruits
            items = self.expression()
            self.end_of_line()
            return N.ForEach(var, items, self.loop_body(tok), line=line, column=col)
        count = self.expression()                                # loop 3
        self.end_of_line()
        return N.RepeatTimes(count, self.loop_body(tok), line=line, column=col)

    def stmt_while(self):
        self.fail("Write 'loop while ...' to repeat while something is true.")

    def stmt_fn(self):
        tok = self.next()
        name = self.expect_name("a name for the function").value
        params = []
        if self.at("SYMBOL", "("):
            self.fail("Write the inputs without brackets, separated by spaces.",
                      hint=f"Like: fn {name} a b")
        while not self.at_line_end():
            if self.at("SYMBOL", ":"):
                self.end_of_line()             # gives the "no ':' needed" hint
            if self.at("SYMBOL", ","):
                self.fail("Separate the inputs with spaces, not commas.", hint=f"Like: fn {name} a b")
            p = self.expect_name("an input name").value
            if p in params:
                self.fail(f"The input '{p}' is listed twice.")
            params.append(p)
        self.end_of_line()
        saved_loop = self.loop_depth
        self.loop_depth = 0
        self.func_depth += 1
        try:
            body = self.block("fn", tok)
        finally:
            self.func_depth -= 1
            self.loop_depth = saved_loop
        self.close_block()
        return N.Define(name, params, body, line=tok.line, column=tok.column)

    def stmt_ret(self):
        tok = self.next()
        if self.func_depth == 0:
            self.fail("'ret' can only be used inside an 'fn' block.", tok)
        value = None if self.at_line_end() else self.expression()
        self.end_of_line()
        return N.Return(value, line=tok.line, column=tok.column)

    def stmt_stop(self):
        tok = self.next()
        if self.loop_depth == 0:
            self.fail("'stop' can only be used inside a 'loop'.", tok)
        self.end_of_line()
        return N.Stop(line=tok.line, column=tok.column)

    def stmt_skip(self):
        tok = self.next()
        if self.loop_depth == 0:
            self.fail("'skip' can only be used inside a 'loop'.", tok)
        self.end_of_line()
        return N.Skip(line=tok.line, column=tok.column)

    def stmt_else(self):
        self.fail("This 'else' is not inside a 'when' or 'pick'.")

    # -- error handling ----------------------------------------------------
    def stmt_try(self):
        tok = self.next()
        self.end_of_line()
        body = self.block("try", tok, stop_words=("fail",))
        if not self.at_kw("fail"):
            self.fail("A 'try' block needs a 'fail' part that says what to do when something goes wrong.",
                      hint="Write it like:  try ... fail why ... .")
        self.next()
        err_name = None
        if not self.at_line_end():
            err_name = self.expect_name("a name for the problem message").value
        self.end_of_line()
        handler = self.block("try", tok)
        self.close_block()
        return N.Try(body, err_name, handler, line=tok.line, column=tok.column)

    def stmt_fail(self):
        self.fail("'fail' belongs inside a 'try' block.",
                  hint="To stop with your own message, write: oops \"message\"")

    def stmt_oops(self):
        tok = self.next()
        if self.at_line_end():
            self.fail("'oops' needs a message.", hint='Write it like: oops "Not enough money"')
        message = self.expression()
        self.end_of_line()
        return N.Oops(message, line=tok.line, column=tok.column)

    # -- pattern matching ----------------------------------------------------
    def stmt_pick(self):
        tok = self.next()
        if self.at_line_end():
            self.fail("'pick' needs a value to look at.", hint="Write it like: pick day")
        value = self.expression()
        self.end_of_line()
        self.skip_newlines()
        cases, else_body = [], None
        if not self.at_kw("is"):
            self.fail("After 'pick', each choice starts with 'is'.", hint='Like:  is "sat", "sun"')
        while self.at_kw("is"):
            self.next()
            patterns = [self.expression()]
            while self.at("SYMBOL", ","):
                self.next()
                patterns.append(self.expression())
            self.end_of_line()
            body = self.block("pick", tok, stop_at_else=True, stop_words=("is",))
            cases.append((patterns, body))
        if self.at_kw("else"):
            self.next()
            self.end_of_line()
            else_body = self.block("pick", tok, stop_words=("is",))
            if self.at_kw("is"):
                self.fail("'else' must be the last choice in a 'pick'.")
        self.close_block()
        return N.Pick(value, cases, else_body, line=tok.line, column=tok.column)

    def stmt_is(self):
        self.fail("'is' is used inside a 'pick' block.",
                  hint="To compare two values, use = (for example: when x = 5)")

    # -- files, memory, tasks ------------------------------------------------
    def stmt_use(self):
        tok = self.next()
        if not self.at("TEXT"):
            self.fail("'use' needs the file name in quotes.", hint='Write it like: use "shapes.simp"')
        path = self.expression()
        self.end_of_line()
        return N.Use(path, line=tok.line, column=tok.column)

    def stmt_keep(self):
        tok = self.next()
        name = self.expect_name("a variable name").value
        if self.at_line_end():
            self.fail("'keep' needs a starting value for the first run.", hint=f"Write it like: keep {name} 0")
        default = self.expression()
        self.end_of_line()
        return N.Keep(name, default, line=tok.line, column=tok.column)

    def stmt_task(self):
        tok = self.next()
        name = self.expect_name("a name for the task").value
        self.end_of_line()
        saved_loop = self.loop_depth
        self.loop_depth = 0
        self.func_depth += 1
        try:
            body = self.block("task", tok)
        finally:
            self.func_depth -= 1
            self.loop_depth = saved_loop
        self.close_block()
        return N.Task(name, body, line=tok.line, column=tok.column)

    def stmt_await(self):
        tok = self.tok
        expr = self.primary()
        self.end_of_line()
        return N.ExprStatement(expr, line=tok.line, column=tok.column)

    def expression_statement(self):
        tok = self.tok
        expr = self.expression()
        if not isinstance(expr, (N.Call, N.Await, N.Pipe)):
            hint = "To show a value write: out ...   To store one: let name value"
            raise SyntaxProblem("This line doesn't tell me to do anything.",
                                tok.line, tok.column, hint)
        self.end_of_line()
        return N.ExprStatement(expr, line=tok.line, column=tok.column)

    # -- expressions (lowest to highest priority) -------------------------
    def expression(self):
        value = self.or_expr()
        if not self.at("SYMBOL", "|"):
            return value
        tok = self.tok
        stages = []
        while self.at("SYMBOL", "|"):
            self.next()
            if self.at("NAME", "only") or self.at("NAME", "each"):
                word = self.next().value
                if self.at_line_end() or self.at("SYMBOL", "|"):
                    self.fail(f"'{word}' needs something to work out for every item.",
                              hint="Use 'it' for the item, like: | only it > 3   or   | each it * 2")
                stages.append((word, self.or_expr()))
                continue
            if not self.at("NAME"):
                self.fail("After '|' write 'only', 'each', or a function name.",
                          hint="Like: scores | only it > 50 | each it * 2 | sort")
            name = self.next()
            callee = N.Name(name.value, line=name.line, column=name.column)
            args = []
            if self.at("SYMBOL", "(") and not self.tok.spaced:
                self.next()
                while not self.at("SYMBOL", ")"):
                    args.append(self.or_expr())
                    if not self.at("SYMBOL", ","):
                        break
                    self.next()
                self.expect_sym(")")
            stages.append(("call", callee, args))
        return N.Pipe(value, stages, line=tok.line, column=tok.column)

    def or_expr(self):
        left = self.and_expr()
        while self.at_kw("or"):
            tok = self.next()
            left = N.Binary("or", left, self.and_expr(), line=tok.line, column=tok.column)
        return left

    def and_expr(self):
        left = self.not_expr()
        while self.at_kw("and"):
            tok = self.next()
            left = N.Binary("and", left, self.not_expr(), line=tok.line, column=tok.column)
        return left

    def not_expr(self):
        if self.at_kw("not"):
            tok = self.next()
            return N.Unary("not", self.not_expr(), line=tok.line, column=tok.column)
        return self.comparison()

    def compare_op(self):
        """Return the comparison operator at the cursor (consuming it), or None."""
        if self.at("SYMBOL") and self.tok.value in COMPARE_OPS:
            return self.next().value
        if self.at_kw("has"):
            self.next()
            return "has"
        if self.at_kw("is"):
            self.fail("To compare two values, use = instead of 'is'.",
                      hint="Like: when x = 5   ('is' is only used inside a 'pick' block)")
        return None

    def comparison(self):
        left = self.range_expr()
        tok = self.tok
        op = self.compare_op()
        if op is None:
            return left
        right = self.range_expr()
        node = N.Binary(op, left, right, line=tok.line, column=tok.column)
        second = self.tok
        if self.compare_op() is not None:
            self.fail("You can only compare two things at a time.", second,
                      hint="Join comparisons with 'and', like: x > 1 and x < 10")
        return node

    def range_expr(self):
        left = self.additive()
        if self.at("SYMBOL", ".."):
            tok = self.next()
            right = self.additive()
            left = N.Binary("..", left, right, line=tok.line, column=tok.column)
            if self.at("SYMBOL", ".."):
                self.fail("A range has only a start and an end, like 1..10")
        return left

    def additive(self):
        left = self.multiplicative()
        while self.at("SYMBOL") and self.tok.value in ("+", "-"):
            tok = self.next()
            left = N.Binary(tok.value, left, self.multiplicative(), line=tok.line, column=tok.column)
        return left

    def multiplicative(self):
        left = self.unary()
        while (self.at("SYMBOL") and self.tok.value in ("*", "/")) or self.at_kw("mod"):
            tok = self.next()
            left = N.Binary(tok.value, left, self.unary(), line=tok.line, column=tok.column)
        return left

    def unary(self):
        if self.at("SYMBOL", "-"):
            tok = self.next()
            return N.Unary("-", self.unary(), line=tok.line, column=tok.column)
        return self.postfix()

    def postfix(self):
        expr = self.primary()
        while True:
            if self.at_field():
                dot = self.next()
                expr = N.Field(expr, self.next().value, line=dot.line, column=dot.column)
                continue
            if not (self.at("SYMBOL") and self.tok.value in ("(", "[") and not self.tok.spaced):
                return expr
            tok = self.next()
            if tok.value == "(":
                args = []
                while not self.at("SYMBOL", ")"):
                    args.append(self.expression())
                    if not self.at("SYMBOL", ","):
                        break
                    self.next()
                self.expect_sym(")", hint="Separate values with commas, like: max(1, 2)")
                expr = N.Call(expr, args, line=tok.line, column=tok.column)
            else:
                index = self.expression()
                self.expect_sym("]")
                expr = N.Index(expr, index, line=tok.line, column=tok.column)

    def primary(self):
        tok = self.tok
        if tok.kind == "NUMBER":
            self.next()
            return N.Literal(tok.value, line=tok.line, column=tok.column)
        if tok.kind == "TEXT":
            self.next()
            return self.text_node(tok)
        if tok.kind == "NAME":
            self.next()
            return N.Name(tok.value, line=tok.line, column=tok.column)
        if tok.kind == "KEYWORD" and tok.value in ("true", "false", "none"):
            self.next()
            value = {"true": True, "false": False, "none": None}[tok.value]
            return N.Literal(value, line=tok.line, column=tok.column)
        if self.at("SYMBOL", "("):
            self.next()
            expr = self.expression()
            self.expect_sym(")")
            return expr
        if self.at("SYMBOL", "{"):
            return self.map_literal()
        if tok.kind == "KEYWORD" and tok.value == "fn":
            self.next()
            params = []
            while self.at("NAME"):
                params.append(self.next().value)
            self.expect_sym("->", hint="A quick function looks like: fn n -> n * 2")
            body = self.expression()
            return N.Lambda(params, body, line=tok.line, column=tok.column)
        if tok.kind == "KEYWORD" and tok.value == "await":
            self.next()
            name = self.expect_name("the name of a task")
            return N.Await(name.value, line=tok.line, column=tok.column)
        if self.at("SYMBOL", "["):
            self.next()
            items = []
            while not self.at("SYMBOL", "]"):
                items.append(self.expression())
                if not self.at("SYMBOL", ","):
                    break
                self.next()
            self.expect_sym("]", hint="Separate list items with commas, like: [1, 2, 3]")
            return N.ListLiteral(items, line=tok.line, column=tok.column)
        if tok.kind == "KEYWORD":
            self.fail(f"I didn't expect the word '{tok.value}' here.",
                      hint=f"'{tok.value}' is a SimpleTalk word, so it can't be used as a variable name.")
        if self.at_line_end():
            self.fail("I expected a value here, but the line ended.")
        self.fail(f"I expected a value here, but found {self.describe(tok)}.")

    def map_literal(self):
        tok = self.next()
        items, seen = [], set()
        while not self.at("SYMBOL", "}"):
            key_tok = self.tok
            if key_tok.kind in ("NAME", "KEYWORD"):
                key = self.next().value
            elif key_tok.kind == "TEXT" and all(isinstance(p, str) for p in key_tok.value.parts):
                key = "".join(key_tok.value.parts)
                self.next()
            else:
                self.fail("A map key must be a name or plain text, like {name: \"Bicky\"}.")
            if key in seen:
                self.fail(f"The key '{key}' appears twice in this map.", key_tok)
            seen.add(key)
            self.expect_sym(":", hint="Write each entry as  key: value")
            items.append((key, self.expression()))
            if not self.at("SYMBOL", ","):
                break
            self.next()
        self.expect_sym("}", hint="Separate entries with commas, like: {name: \"Bicky\", age: 20}")
        return N.MapLiteral(items, line=tok.line, column=tok.column)

    def text_node(self, tok):
        value: TextValue = tok.value
        parts = []
        for part in value.parts:
            if isinstance(part, TextPart):
                sub = Parser(tokenize(part.code, part.line - 1, part.column - 1))
                expr = sub.expression()
                if not sub.at_line_end():
                    sub.fail("I couldn't understand the code inside { }.")
                parts.append(expr)
            else:
                parts.append(part)
        if len(parts) == 1 and isinstance(parts[0], str):
            return N.Literal(parts[0], line=tok.line, column=tok.column)
        return N.Text(parts, line=tok.line, column=tok.column)


def parse(source):
    return Parser(tokenize(source), source).parse_program()
