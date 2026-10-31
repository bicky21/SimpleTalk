"""The `simpletalk` command.

    simpletalk hello.simp             run a program
    simpletalk --explain hello.simp   read the program back in plain English
    simpletalk --trace hello.simp     run it one step at a time, showing each line
    simpletalk --check hello.simp     only check it for mistakes
    simpletalk                        open the interactive playground
"""

import argparse
import errno
import os
import sys

from . import __version__
from . import nodes as N
from .errors import SimpleTalkError, SyntaxProblem
from .explain import explain
from .interpreter import Interpreter
from .lexer import tokenize
from .parser import Parser
from .values import show

BANNER = f"""SimpleTalk {__version__} - type code and press Enter.
Type 'help' for a quick guide, or 'quit' to leave."""

HELP = """Quick guide (short words, blocks end with a '.' line):
  out "Hello"                   show something
  let age 12                    store a value
  up age                        add 1 to a number (up age 5 adds 5)
  in name "Your name?"          ask the user (in age num "Age?" insists on a number)
  when age > 10 ... else ... .  make a decision
  loop 3 ... .                  do something 3 times
  loop i 1..10 ... .            count
  loop x my_list ... .          go through a list
  fn greet name ... .           make your own function
  watch age                     report every change to age
  test 2 + 2 = 4                check that something is true
Type the block's lines, then a line with just '.' to run it."""


def read_source(path):
    try:
        with open(path, encoding="utf-8-sig") as f:
            return f.read()
    except FileNotFoundError:
        print(f"Oops! I can't find the file '{path}'.", file=sys.stderr)
    except (IsADirectoryError, PermissionError, UnicodeDecodeError) as err:
        print(f"Oops! I can't read '{path}': {err}", file=sys.stderr)
    return None


def run_file(path, mode="run"):
    source = read_source(path)
    if source is None:
        return 2

    interp = None
    try:
        program = Parser(tokenize(source), source).parse_program()
        if mode == "check":
            print(f"Looks good! No mistakes found in {path}.")
            return 0
        if mode == "explain":
            print(f"What {path} does:\n")
            print(explain(program))
            return 0
        trace = None
        if mode == "trace":
            lines = source.replace("\r\n", "\n").split("\n")

            def trace(line):
                code = lines[line - 1].strip() if 1 <= line <= len(lines) else ""
                print(f"  > line {line:<3} | {code}", flush=True)
        interp = Interpreter(trace=trace, program_path=path)
        interp.source, interp.filename = source, path
        interp.run(program)
    except SimpleTalkError as err:
        report_tests(interp)
        print(err.pretty(source, path), file=sys.stderr)
        return 1
    except KeyboardInterrupt:
        print("\nStopped.", file=sys.stderr)
        return 130
    report_tests(interp)
    return 0


def report_tests(interp):
    if interp is not None and interp.tests_passed:
        n = interp.tests_passed
        print(f"[test] {n} test{'s' if n != 1 else ''} passed.")


def try_expression(source):
    """In the playground, `2 + 2` should just show 4. Returns a node or None."""
    try:
        p = Parser(tokenize(source), source)
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
                value = interp.evaluate(expr)
                if value is not None or not isinstance(expr, N.Call):
                    print(show(value, nested=True))
            else:
                program = Parser(tokenize(source), source).parse_program()
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
    try:
        return _main(argv)
    except OSError as err:
        # The output went to a command that stopped reading (like `| head`).
        # That's not a problem with the program, so finish quietly.
        # (Linux reports a broken pipe; Windows reports "invalid argument".)
        if not isinstance(err, BrokenPipeError) and err.errno not in (errno.EPIPE, errno.EINVAL):
            raise
        try:
            devnull = os.open(os.devnull, os.O_WRONLY)
            os.dup2(devnull, sys.stdout.fileno())
        except (OSError, ValueError):
            pass
        return 0


def _main(argv=None):
    ap = argparse.ArgumentParser(prog="simpletalk",
                                 description="Run SimpleTalk programs (.simp files).")
    ap.add_argument("file", nargs="?", help="the .simp program to run")
    group = ap.add_mutually_exclusive_group()
    group.add_argument("--explain", action="store_true",
                       help="describe the program in plain English (without running it)")
    group.add_argument("--trace", action="store_true",
                       help="run the program and show each line as it runs")
    group.add_argument("--check", action="store_true", help="only check the program for mistakes")
    ap.add_argument("--version", action="version", version=f"SimpleTalk {__version__}")
    args = ap.parse_args(argv)
    mode = "explain" if args.explain else "trace" if args.trace else "check" if args.check else "run"
    if args.file:
        return run_file(args.file, mode)
    if mode != "run":
        ap.error(f"--{mode} needs a file name")
    return repl()


if __name__ == "__main__":
    raise SystemExit(main())
