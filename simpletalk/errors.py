"""Friendly error messages for SimpleTalk.

Every error SimpleTalk shows has three parts:
  1. WHERE it happened (line number + the line itself, with a ^ marker)
  2. WHAT went wrong, in plain English
  3. A HINT on how to fix it (when we can guess one)
"""

import difflib


class SimpleTalkError(Exception):
    """Base class for every error SimpleTalk shows to the user."""

    kind = "Problem"

    def __init__(self, message, line=None, column=None, hint=None):
        super().__init__(message)
        self.message = message
        self.line = line
        self.column = column
        self.hint = hint
        self.source = None      # set when the problem is in another file (see `use`)
        self.filename = None

    def pretty(self, source=None, filename=None):
        """Return a friendly, multi-line description of the error."""
        if self.source is not None:            # the problem is inside a `use`d file
            source, filename = self.source, self.filename
        where = ""
        if self.line is not None:
            where = f" on line {self.line}"
            if filename:
                where += f" of {filename}"
        out = [f"Oops! {self.kind}{where}:"]

        if source is not None and self.line is not None:
            lines = source.splitlines()
            if 1 <= self.line <= len(lines):
                code = lines[self.line - 1]
                out.append("")
                out.append(f"    {self.line} | {code}")
                if self.column is not None:
                    pad = " " * (len(str(self.line)) + 3 + self.column - 1)
                    out.append(f"    {pad}^")
                out.append("")

        out.append(f"  {self.message}")
        if self.hint:
            out.append(f"  Hint: {self.hint}")
        return "\n".join(out)

    def __str__(self):
        return self.pretty()


class SyntaxProblem(SimpleTalkError):
    """The code is not written the way SimpleTalk expects."""

    kind = "I could not understand the code"

    def __init__(self, message, line=None, column=None, hint=None, incomplete=False):
        super().__init__(message, line, column, hint)
        # True when the code just isn't finished yet (used by the REPL to
        # keep reading more lines instead of showing an error).
        self.incomplete = incomplete


class RuntimeProblem(SimpleTalkError):
    """The code is valid, but something went wrong while running it."""

    kind = "Something went wrong while running"


class UserProblem(RuntimeProblem):
    """Raised by the program itself with `oops "message"`."""

    kind = "The program stopped"


def did_you_mean(word, choices):
    """Suggest the closest spelling, e.g. 'nmae' -> 'name'."""
    matches = difflib.get_close_matches(word, list(choices), n=1, cutoff=0.6)
    if matches:
        return f"Did you mean '{matches[0]}'?"
    return None
