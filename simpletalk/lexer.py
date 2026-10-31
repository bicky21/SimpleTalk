"""Step 1 of running a program: turn text into a list of tokens.

A token is one small "word" of the program, for example:
    say "Hi {name}"   ->   KEYWORD(say)  TEXT("Hi ", {name})  NEWLINE
"""

from dataclasses import dataclass, field

from .errors import SyntaxProblem

# Every reserved word in SimpleTalk. Kept deliberately short so it is
# easy to remember. Changing this list is a breaking change.
KEYWORDS = {
    # talking
    "say", "ask", "into",
    # variables and lists
    "set", "to", "change", "by", "add", "remove", "from",
    # decisions
    "if", "then", "else", "end",
    # loops
    "repeat", "times", "while", "until", "forever", "for", "each", "in",
    "stop", "skip",
    # functions
    "define", "return",
    # logic and values
    "and", "or", "not", "is", "mod", "true", "false", "nothing",
}

# Two-character symbols must be listed before one-character ones.
SYMBOLS = ["!=", "<=", ">=", "+", "-", "*", "/", "=", "<", ">",
           "(", ")", "[", "]", ","]


@dataclass
class Token:
    kind: str          # NUMBER, TEXT, NAME, KEYWORD, SYMBOL, NEWLINE, EOF
    value: object
    line: int
    column: int

    def __repr__(self):
        return f"{self.kind}({self.value!r})@{self.line}:{self.column}"


@dataclass
class TextPart:
    """A piece of code inside {braces} in a text, e.g. "Hi {name}"."""
    code: str
    line: int
    column: int


@dataclass
class TextValue:
    parts: list = field(default_factory=list)   # mix of str and TextPart


class Lexer:
    def __init__(self, source, line_offset=0, column_offset=0):
        # Normalise Windows / old Mac line endings and tabs.
        self.src = source.replace("\r\n", "\n").replace("\r", "\n")
        self.pos = 0
        self.line = 1 + line_offset
        self.col = 1 + column_offset
        self.tokens = []
        self.depth = 0   # how many ( or [ are open; newlines are ignored inside

    # -- small helpers -------------------------------------------------
    def peek(self, ahead=0):
        i = self.pos + ahead
        return self.src[i] if i < len(self.src) else ""

    def advance(self):
        ch = self.src[self.pos]
        self.pos += 1
        if ch == "\n":
            self.line += 1
            self.col = 1
        else:
            self.col += 1
        return ch

    def add(self, kind, value, line, col):
        self.tokens.append(Token(kind, value, line, col))

    # -- main loop -----------------------------------------------------
    def tokenize(self):
        while self.pos < len(self.src):
            ch = self.peek()
            line, col = self.line, self.col

            if ch in " \t":
                self.advance()
            elif ch == "#":
                while self.peek() and self.peek() != "\n":
                    self.advance()
            elif ch == "\n":
                self.advance()
                if self.depth == 0 and self.tokens and self.tokens[-1].kind != "NEWLINE":
                    self.add("NEWLINE", "\n", line, col)
            elif ch.isdigit() or (ch == "." and self.peek(1).isdigit()):
                self.read_number(line, col)
            elif ch in "\"'":
                self.read_text(line, col)
            elif ch.isalpha() or ch == "_":
                self.read_word(line, col)
            else:
                self.read_symbol(line, col)

        if self.depth > 0:
            raise SyntaxProblem("A bracket was opened but never closed.",
                                self.line, None,
                                "Every ( needs a ) and every [ needs a ].",
                                incomplete=True)
        if self.tokens and self.tokens[-1].kind != "NEWLINE":
            self.add("NEWLINE", "\n", self.line, self.col)
        self.add("EOF", None, self.line, self.col)
        return self.tokens

    # -- token readers -------------------------------------------------
    def read_number(self, line, col):
        text = ""
        seen_dot = False
        while self.peek().isdigit() or self.peek() == "_" or (
                self.peek() == "." and not seen_dot and self.peek(1).isdigit()):
            if self.peek() == ".":
                seen_dot = True
            text += self.advance()
        if self.peek().isalpha():
            raise SyntaxProblem(f"'{text}{self.peek()}...' is not a valid number or name.",
                                line, col, "Names cannot start with a digit.")
        text = text.replace("_", "")
        self.add("NUMBER", float(text) if seen_dot else int(text), line, col)

    def read_word(self, line, col):
        word = ""
        while self.peek().isalnum() or self.peek() == "_":
            word += self.advance()
        lower = word.lower()
        if lower in KEYWORDS:
            # Keywords are case-insensitive: SAY, Say and say all work.
            self.add("KEYWORD", lower, line, col)
        else:
            self.add("NAME", word, line, col)

    def read_symbol(self, line, col):
        for sym in SYMBOLS:
            if self.src.startswith(sym, self.pos):
                for _ in sym:
                    self.advance()
                if sym in "([":
                    self.depth += 1
                elif sym in ")]":
                    self.depth = max(0, self.depth - 1)
                self.add("SYMBOL", sym, line, col)
                return
        ch = self.peek()
        hint = None
        if ch == "{" or ch == "}":
            hint = "Curly braces { } are only used inside text, like \"Hi {name}\"."
        elif ch == "%":
            hint = "Use the word 'mod' for remainders, like: 10 mod 3"
        elif ch in "“”‘’":
            hint = "That looks like a 'smart quote'. Use plain \" quotes instead."
        raise SyntaxProblem(f"I don't know what the symbol '{ch}' means.", line, col, hint)

    def read_text(self, line, col):
        quote = self.advance()
        parts = []
        buf = ""
        escapes = {"n": "\n", "t": "\t", "\\": "\\", '"': '"', "'": "'",
                   "{": "{", "}": "}"}
        while True:
            ch = self.peek()
            if ch == "" or ch == "\n":
                raise SyntaxProblem("This text was never closed.", line, col,
                                    f"Add a closing {quote} at the end of the text.")
            if ch == quote:
                self.advance()
                break
            if ch == "\\":
                self.advance()
                nxt = self.peek()
                if nxt in escapes:
                    self.advance()
                    buf += escapes[nxt]
                else:
                    buf += "\\"
                continue
            if ch == "{":
                if self.peek(1) == "{":      # {{ means a real brace
                    self.advance(); self.advance()
                    buf += "{"
                    continue
                if buf:
                    parts.append(buf)
                    buf = ""
                self.advance()
                pline, pcol = self.line, self.col
                code = ""
                while self.peek() not in ("}", "", "\n"):
                    code += self.advance()
                if self.peek() != "}":
                    raise SyntaxProblem("A { inside this text was never closed.",
                                        pline, pcol - 1, "Add a } after the name.")
                self.advance()
                if not code.strip():
                    raise SyntaxProblem("Empty {} inside text.", pline, pcol - 1,
                                        "Put a name inside, like {name}, or write {{ for a brace.")
                parts.append(TextPart(code, pline, pcol))
                continue
            if ch == "}" and self.peek(1) == "}":
                self.advance(); self.advance()
                buf += "}"
                continue
            buf += self.advance()
        if buf or not parts:
            parts.append(buf)
        self.add("TEXT", TextValue(parts), line, col)


def tokenize(source, line_offset=0, column_offset=0):
    return Lexer(source, line_offset, column_offset).tokenize()
