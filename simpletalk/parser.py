"""Step 2: turn the list of tokens into a tree of nodes (the program's structure).

The grammar is small on purpose. Every block starts with a keyword and is
closed with `end` (you may write `end if`, `end repeat`, ... to be extra clear).
"""

from . import nodes as N
from .errors import SyntaxProblem
from .lexer import TextPart, TextValue, tokenize

BLOCK_WORDS = {"if", "repeat", "for", "define"}
COMPARE_OPS = {"=", "!=", "<", ">", "<=", ">="}


class Parser:
    def __init__(self, tokens):
        self.tokens = tokens
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

    def expect_kw(self, word, hint=None):
        if not self.at_kw(word):
            self.fail(f"I expected the word '{word}' here, but found {self.describe(self.tok)}.",
                      hint=hint)
        return self.next()

    def expect_sym(self, sym, hint=None):
        if not self.at("SYMBOL", sym):
            self.fail(f"I expected '{sym}' here, but found {self.describe(self.tok)}.", hint=hint)
        return self.next()

    def expect_name(self, what="a name"):
        if self.tok.kind == "KEYWORD":
            self.fail(f"'{self.tok.value}' is a SimpleTalk word, so it can't be used as {what}.",
                      hint="Pick a different name, e.g. add 'my' in front: my_" + self.tok.value)
        if self.tok.kind != "NAME":
            self.fail(f"I expected {what} here, but found {self.describe(self.tok)}.")
        return self.next()

    def end_of_line(self):
        if self.at("NEWLINE"):
            self.next()
            return
        if self.at("EOF"):
            return
        self.fail(f"I didn't expect {self.describe(self.tok)} here.",
                  hint="Each instruction goes on its own line.")

    def skip_newlines(self):
        while self.at("NEWLINE"):
            self.next()

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
            if self.at_kw("end"):
                self.fail("This 'end' has nothing to close.",
                          hint="Remove it, or check the block above was opened correctly.")
            if self.at_kw("else"):
                self.fail("This 'else' is not inside an 'if'.")
            body.append(self.statement())
            self.skip_newlines()
        return body

    def block(self, opener, open_tok, stop_at_else=False):
        """Read statements until `end` (and `else` when inside an if)."""
        body = []
        self.skip_newlines()
        while True:
            if self.at("EOF"):
                raise SyntaxProblem(
                    f"The '{opener}' that starts on line {open_tok.line} was never closed.",
                    open_tok.line, open_tok.column, f"Add 'end {opener}' after the block.",
                    incomplete=True)
            if self.at_kw("end"):
                return body
            if self.at_kw("else"):
                if stop_at_else:
                    return body
                self.fail("This 'else' is not inside an 'if'.")
            body.append(self.statement())
            self.skip_newlines()

    def close_block(self, opener):
        end_tok = self.expect_kw("end")
        if self.tok.kind == "KEYWORD" and self.tok.value in BLOCK_WORDS:
            if self.tok.value != opener:
                self.fail(f"This says 'end {self.tok.value}', but the open block is an '{opener}'.",
                          hint=f"Change it to 'end {opener}'.")
            self.next()
        self.end_of_line()
        return end_tok

    # -- statements ------------------------------------------------------
    def statement(self):
        tok = self.tok
        if tok.kind == "KEYWORD":
            handler = getattr(self, f"stmt_{tok.value}", None)
            if handler:
                node = handler()
                return node
        node = self.expression_statement()
        return node

    def stmt_say(self):
        tok = self.next()
        if self.at("NEWLINE") or self.at("EOF"):
            self.fail("'say' needs something to say.", hint='Try: say "Hello!"')
        values = [self.expression()]
        while self.at("SYMBOL", ","):
            self.next()
            values.append(self.expression())
        self.end_of_line()
        return N.Say(values, line=tok.line, column=tok.column)

    def stmt_ask(self):
        tok = self.next()
        prompt = self.expression()
        self.expect_kw("into", hint='Write it like: ask "What is your name?" into name')
        name = self.expect_name("a variable name").value
        self.end_of_line()
        return N.Ask(prompt, name, line=tok.line, column=tok.column)

    def stmt_set(self):
        tok = self.next()
        target = self.postfix()
        if not isinstance(target, (N.Name, N.Index)):
            self.fail("After 'set' I expected a variable name, like: set score to 10", tok)
        if self.at("SYMBOL", "="):
            self.fail("Use 'to' instead of '=' when setting a variable.",
                      hint="Write it like: set score to 10")
        self.expect_kw("to", hint="Write it like: set score to 10")
        value = self.expression()
        self.end_of_line()
        return N.Set(target, value, line=tok.line, column=tok.column)

    def stmt_change(self):
        tok = self.next()
        name = self.expect_name("a variable name").value
        self.expect_kw("by", hint="Write it like: change score by 1")
        amount = self.expression()
        self.end_of_line()
        return N.Change(name, amount, line=tok.line, column=tok.column)

    def stmt_add(self):
        tok = self.next()
        value = self.expression()
        self.expect_kw("to", hint="Write it like: add \"milk\" to shopping")
        target = self.postfix()
        self.end_of_line()
        return N.Add(value, target, line=tok.line, column=tok.column)

    def stmt_remove(self):
        tok = self.next()
        value = self.expression()
        self.expect_kw("from", hint="Write it like: remove \"milk\" from shopping")
        target = self.postfix()
        self.end_of_line()
        return N.Remove(value, target, line=tok.line, column=tok.column)

    def condition_line(self):
        cond = self.expression()
        if self.at_kw("then"):
            self.next()
        if not self.at("NEWLINE"):
            self.fail(f"I didn't expect {self.describe(self.tok)} here.",
                      hint="Put the code that should run on the next line, and close it with 'end if'.")
        return cond

    def stmt_if(self):
        tok = self.next()
        branches = []
        cond = self.condition_line()
        body = self.block("if", tok, stop_at_else=True)
        branches.append((cond, body))
        else_body = None
        while self.at_kw("else"):
            else_tok = self.next()
            if self.at_kw("if"):
                self.next()
                cond = self.condition_line()
                body = self.block("if", tok, stop_at_else=True)
                branches.append((cond, body))
                continue
            if not self.at("NEWLINE"):
                self.fail("Put the code for 'else' on the next line.", else_tok)
            else_body = self.block("if", tok, stop_at_else=True)
            if self.at_kw("else"):
                self.fail("An 'if' can only have one plain 'else', and it must come last.")
            break
        self.close_block("if")
        return N.If(branches, else_body, line=tok.line, column=tok.column)

    def loop_body(self, opener, open_tok):
        self.loop_depth += 1
        try:
            body = self.block(opener, open_tok)
        finally:
            self.loop_depth -= 1
        self.close_block(opener)
        return body

    def stmt_repeat(self):
        tok = self.next()
        if self.at_kw("while", "until"):
            until = self.next().value == "until"
            cond = self.expression()
            self.end_of_line()
            body = self.loop_body("repeat", tok)
            return N.RepeatWhile(cond, body, until, line=tok.line, column=tok.column)
        if self.at_kw("forever"):
            self.next()
            self.end_of_line()
            body = self.loop_body("repeat", tok)
            return N.RepeatWhile(None, body, line=tok.line, column=tok.column)
        if self.at("NEWLINE"):
            self.fail("How many times should I repeat?",
                      hint="Try: repeat 3 times, repeat while x < 10, or repeat forever")
        count = self.expression()
        self.expect_kw("times", hint="Write it like: repeat 3 times")
        self.end_of_line()
        body = self.loop_body("repeat", tok)
        return N.RepeatTimes(count, body, line=tok.line, column=tok.column)

    def stmt_for(self):
        tok = self.next()
        if self.at_kw("each"):
            self.next()
            var = self.expect_name("a variable name").value
            self.expect_kw("in", hint="Write it like: for each fruit in fruits")
            iterable = self.expression()
            self.end_of_line()
            body = self.loop_body("for", tok)
            return N.ForEach(var, iterable, body, line=tok.line, column=tok.column)
        var = self.expect_name("a variable name").value
        self.expect_kw("from", hint="Write it like: for i from 1 to 10  (or: for each x in my_list)")
        start = self.expression()
        self.expect_kw("to", hint="Write it like: for i from 1 to 10")
        end = self.expression()
        self.end_of_line()
        body = self.loop_body("for", tok)
        return N.ForRange(var, start, end, body, line=tok.line, column=tok.column)

    def stmt_define(self):
        tok = self.next()
        name = self.expect_name("a name for the function").value
        params = []
        if self.at("SYMBOL", "("):
            self.next()
            while not self.at("SYMBOL", ")"):
                p = self.expect_name("a parameter name").value
                if p in params:
                    self.fail(f"The parameter '{p}' is listed twice.")
                params.append(p)
                if not self.at("SYMBOL", ","):
                    break
                self.next()
            self.expect_sym(")")
        self.end_of_line()
        saved_loop = self.loop_depth
        self.loop_depth = 0
        self.func_depth += 1
        try:
            body = self.block("define", tok)
        finally:
            self.func_depth -= 1
            self.loop_depth = saved_loop
        self.close_block("define")
        return N.Define(name, params, body, line=tok.line, column=tok.column)

    def stmt_return(self):
        tok = self.next()
        if self.func_depth == 0:
            self.fail("'return' can only be used inside a 'define' block.", tok)
        value = None
        if not (self.at("NEWLINE") or self.at("EOF")):
            value = self.expression()
        self.end_of_line()
        return N.Return(value, line=tok.line, column=tok.column)

    def stmt_stop(self):
        tok = self.next()
        if self.loop_depth == 0:
            self.fail("'stop' can only be used inside a loop (repeat or for).", tok)
        self.end_of_line()
        return N.Stop(line=tok.line, column=tok.column)

    def stmt_skip(self):
        tok = self.next()
        if self.loop_depth == 0:
            self.fail("'skip' can only be used inside a loop (repeat or for).", tok)
        self.end_of_line()
        return N.Skip(line=tok.line, column=tok.column)

    def stmt_end(self):
        self.fail("This 'end' has nothing to close.")

    def stmt_else(self):
        self.fail("This 'else' is not inside an 'if'.")

    def expression_statement(self):
        tok = self.tok
        if tok.kind == "NAME" and self.peek().kind == "SYMBOL" and self.peek().value == "=":
            self.fail(f"To store a value, write: set {tok.value} to ...", tok,
                      hint="SimpleTalk uses 'set name to value' instead of '='.")
        expr = self.expression()
        if not isinstance(expr, N.Call):
            hint = None
            if isinstance(expr, N.Name) and self.at("TEXT"):
                hint = f"Did you mean: say {self.describe(self.tok)}?"
            elif isinstance(expr, N.Name):
                hint = "To show a value use 'say', to store one use 'set ... to ...'."
            raise SyntaxProblem("This line doesn't tell me to do anything.",
                                tok.line, tok.column, hint)
        self.end_of_line()
        return N.ExprStatement(expr, line=tok.line, column=tok.column)

    # -- expressions (lowest to highest priority) -------------------------
    def expression(self):
        return self.or_expr()

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
        if self.at_kw("is"):
            self.next()
            if self.at_kw("not"):
                self.next()
                return "!="
            return "="
        if self.at_kw("in"):
            self.next()
            return "in"
        return None

    def comparison(self):
        left = self.additive()
        tok = self.tok
        op = self.compare_op()
        if op is None:
            return left
        right = self.additive()
        node = N.Binary(op, left, right, line=tok.line, column=tok.column)
        second = self.tok
        if self.compare_op() is not None:
            self.fail("You can only compare two things at a time.", second,
                      hint="Join comparisons with 'and', like: x > 1 and x < 10")
        return node

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
            if self.at("SYMBOL", "("):
                tok = self.next()
                args = []
                while not self.at("SYMBOL", ")"):
                    args.append(self.expression())
                    if not self.at("SYMBOL", ","):
                        break
                    self.next()
                self.expect_sym(")", hint="Separate values with commas, like: max(1, 2)")
                expr = N.Call(expr, args, line=tok.line, column=tok.column)
            elif self.at("SYMBOL", "["):
                tok = self.next()
                index = self.expression()
                self.expect_sym("]")
                expr = N.Index(expr, index, line=tok.line, column=tok.column)
            else:
                return expr

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
        if tok.kind == "KEYWORD" and tok.value in ("true", "false", "nothing"):
            self.next()
            value = {"true": True, "false": False, "nothing": None}[tok.value]
            return N.Literal(value, line=tok.line, column=tok.column)
        if self.at("SYMBOL", "("):
            self.next()
            expr = self.expression()
            self.expect_sym(")")
            return expr
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
        self.fail(f"I expected a value here, but found {self.describe(tok)}.")

    def text_node(self, tok):
        value: TextValue = tok.value
        parts = []
        for part in value.parts:
            if isinstance(part, TextPart):
                sub_tokens = tokenize(part.code, part.line - 1, part.column - 1)
                sub = Parser(sub_tokens)
                expr = sub.expression()
                if not sub.at("NEWLINE") and not sub.at("EOF"):
                    sub.fail("I couldn't understand the code inside { }.")
                parts.append(expr)
            else:
                parts.append(part)
        if len(parts) == 1 and isinstance(parts[0], str):
            return N.Literal(parts[0], line=tok.line, column=tok.column)
        return N.Text(parts, line=tok.line, column=tok.column)


def parse(source):
    return Parser(tokenize(source)).parse_program()
