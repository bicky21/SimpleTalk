"""The `simpletalk` command.

    simpletalk hello.simp        run a program
    simpletalk --check hello.simp   only check it for mistakes
    simpletalk                   open the interactive playground
"""

import argparse
import sys

from . import __version__
from . import nodes as N
from .errors import SimpleTalkError, SyntaxProblem
from .interpreter import Interpreter
from .lexer import tokenize
from .parser import Parser
from .values import show

BANNER = f"""SimpleTalk {__version__} - type code and press Enter.
Type 'help' for a quick guide, or 'quit' to leave."""

HELP = """Quick guide:
  say "Hello"                    show something
  set age to 12                  store a value
  change age by 1                add to a number
  ask "Name?" into name          ask the user
  if age > 10 ... end if         make a decision
  repeat 3 times ... end repeat  do something again
  for each x in [1, 2] ... end   go through a list
  define greet(name) ... end     make your own function
Blocks continue on the next lines until you type 'end'."""


def run_file(path, check_only=False):
    try:
        with open(path, encoding="utf-8-sig") as f:
            source = f.read()
    except FileNotFoundError:
        print(f"Oops! I can't find the file '{path}'.", file=sys.stderr)
        return 2
    except (IsADirectoryError, PermissionError, UnicodeDecodeError) as err:
        print(f"Oops! I can't read '{path}': {err}", file=sys.stderr)
        return 2

    try:
        program = Parser(tokenize(source)).parse_program()
        if check_only:
            print(f"Looks good! No mistakes found in {path}.")
            return 0
        Interpreter().run(program)
    except SimpleTalkError as err:
        print(err.pretty(source, path), file=sys.stderr)
        return 1
    except KeyboardInterrupt:
        print("\nStopped.", file=sys.stderr)
        return 130
    return 0


def try_expression(source):
    """In the playground, `2 + 2` should just show 4. Returns a node or None."""
    try:
        p = Parser(tokenize(source))
        p.skip_newlines()
        expr = p.expression()
        p.skip_newlines()
        if p.at("EOF"):
            return expr
    except (SimpleTalkError, RecursionError):
        pass
    return None


def repl():
    print(BANNER)
    interp = Interpreter()
    buffer = []
    while True:
        try:
            line = input("... " if buffer else ">>> ")
        except (EOFError, KeyboardInterrupt):
            print("\nBye!")
            return 0
        if not buffer and line.strip() in ("quit", "exit"):
            print("Bye!")
            return 0
        if not buffer and line.strip() == "help":
            print(HELP)
            continue
        buffer.append(line)
        source = "\n".join(buffer)
        if not source.strip():
            buffer = []
            continue
        try:
            expr = try_expression(source)
            if expr is not None:
                value = interp.eval(expr, interp.globals)
                if value is not None or not isinstance(expr, N.Call):
                    print(show(value, nested=True))
            else:
                program = Parser(tokenize(source)).parse_program()
                interp.run(program)
            buffer = []
        except SyntaxProblem as err:
            if err.incomplete and line.strip():
                continue                 # keep reading the rest of the block
            print(err.pretty(source))
            buffer = []
        except SimpleTalkError as err:
            print(err.pretty(source))
            buffer = []
        except KeyboardInterrupt:
            print("\nStopped.")
            buffer = []


def main(argv=None):
    ap = argparse.ArgumentParser(prog="simpletalk",
                                 description="Run SimpleTalk programs (.simp files).")
    ap.add_argument("file", nargs="?", help="the .simp program to run")
    ap.add_argument("--check", action="store_true", help="only check the program for mistakes")
    ap.add_argument("--version", action="version", version=f"SimpleTalk {__version__}")
    args = ap.parse_args(argv)
    if args.file:
        return run_file(args.file, args.check)
    if args.check:
        ap.error("--check needs a file name")
    return repl()


if __name__ == "__main__":
    raise SystemExit(main())
