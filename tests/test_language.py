"""Tests that lock in how SimpleTalk 2.0 behaves, so it stays stable."""

import pathlib

import pytest

from simpletalk import RuntimeProblem, SyntaxProblem, run
from simpletalk.cli import main
from simpletalk.lexer import KEYWORDS

EXAMPLES = pathlib.Path(__file__).parent.parent / "examples"


def out(source, inputs=()):
    lines = []
    answers = iter(inputs)
    run(source, output=lines.append, input_fn=lambda prompt: next(answers))
    return lines


def problem(source, kind=SyntaxProblem):
    with pytest.raises(kind) as info:
        out(source)
    return info.value


def test_every_keyword_is_tiny():
    assert all(2 <= len(word) <= 5 for word in KEYWORDS)


# ---------------------------------------------------------------- basics
def test_out_text_and_many_values():
    assert out('out "Hello, World!"') == ["Hello, World!"]
    assert out('out "a", 1, true, none, [1, "x"]') == ['a 1 true none [1, "x"]']
    assert out("out") == [""]


def test_empty_lines_and_comments():
    assert out('\n\n;; comment\nout "hi"   ;; trailing\n\n') == ["hi"]


def test_text_interpolation_and_escapes():
    assert out('let n 3\nout "n={n}, double={n * 2}"') == ["n=3, double=6"]
    assert out('out "{{x}} \\"q\\""') == ['{x} "q"']
    assert out("out 'single quotes work'") == ["single quotes work"]


def test_numbers_look_friendly():
    assert out("out 7 / 2, 6 / 3, 0.1 + 0.2, 10 mod 3, -2 * 3") == ["3.5 2 0.3 1 -6"]
    assert out("out 1_000_000") == ["1000000"]


def test_text_plus_anything_joins():
    assert out('out "Age: " + 12') == ["Age: 12"]


def test_let_up_and_in():
    assert out("let x 5\nup x\nup x -3\nout x") == ["3"]
    assert out("let x 1\nlet x x + 1\nout x") == ["2"]
    assert out('in a "Age?"\nout a + 1', ["41"]) == ["42"]
    assert out("in n\nout type(n)", ["Bicky"]) == ["text"]


def test_negative_values_after_names():
    assert out("let x -5\nout x") == ["-5"]
    assert out("let a 10\nlet b a - 3\nout b") == ["7"]


# ---------------------------------------------------------------- decisions
def test_when_else_when_else():
    src = """
let x {}
when x > 10
    out "big"
else when x > 5
    out "medium"
else
    out "small"
.
"""
    assert out(src.format(20)) == ["big"]
    assert out(src.format(7)) == ["medium"]
    assert out(src.format(1)) == ["small"]


def test_comparisons_and_logic():
    assert out('out 1 = 1, 1 != 2, "a" = "a", not false, true and false, true or false') == \
        ["true true true true false true"]
    assert out('out 1 = 1.0, 1 = "1", 1 = true') == ["true false false"]
    assert out("out false and (1 / 0 = 1)") == ["false"]      # short-circuit


# ---------------------------------------------------------------- loops
def test_loop_count_runs_exactly_n_times():
    assert out('loop 3\n out "x"\n.') == ["x"] * 3
    assert out('loop 0\n out "x"\n.') == []
    assert out("let n 2\nloop n\n out 1\n.") == ["1", "1"]
    assert out("let n 2\nloop n * 2\n out 1\n.") == ["1"] * 4


def test_nested_loops():
    assert out('loop 2\n loop 3\n  out "x"\n .\n.') == ["x"] * 6


def test_loop_ranges_count_up_and_down():
    assert out("loop i 1..3\n out i\n.") == ["1", "2", "3"]
    assert out("loop i 3..1\n out i\n.") == ["3", "2", "1"]
    assert out("loop i -1..1\n out i\n.") == ["-1", "0", "1"]
    assert out("let n 3\nloop i 1..n + 1\n out i\n.") == ["1", "2", "3", "4"]
    assert out("loop i 1..10000000\n stop\n.") == []                # lazy, no huge list
    assert out("out 1..4") == ["[1, 2, 3, 4]"]


def test_loop_list_and_text():
    assert out('loop x [1, "b"]\n out x\n.') == ["1", "b"]
    assert out('loop c "hi"\n out c\n.') == ["h", "i"]
    assert out("let l [7, 8]\nloop x l\n out x\n.") == ["7", "8"]


def test_loop_while_forever_stop_skip():
    assert out("let i 0\nloop while i < 3\n up i\n.\nout i") == ["3"]
    src = """
let i 0
loop
    up i
    when i = 2
        skip
    .
    when i > 4
        stop
    .
    out i
.
"""
    assert out(src) == ["1", "3", "4"]


def test_changing_list_while_looping_is_safe():
    assert out("let l [1, 2]\nloop x l\n add l x\n.\nout l") == ["[1, 2, 1, 2]"]


# ---------------------------------------------------------------- lists
def test_lists_are_one_based_with_negative_from_end():
    assert out("let l [10, 20, 30]\nout l[1], l[-1], len(l)") == ["10 30 3"]
    assert out("let l [1, 2]\nlet l[2] 9\nadd l 3\ndel l 1\nout l") == ["[9, 3]"]
    assert out('out ["a", "b"] has "b", "hello" has "ell"') == ["true true"]


def test_space_decides_call_or_value():
    # `let x [1, 2]` is a list, `x[1]` is a position
    assert out("let x [1, 2]\nout x[1]") == ["1"]


# ---------------------------------------------------------------- functions
def test_functions_ret_and_recursion():
    src = """
fn fact n
    when n <= 1
        ret 1
    .
    ret n * fact(n - 1)
.
out fact(10)
"""
    assert out(src) == ["3628800"]


def test_function_without_inputs_or_ret():
    assert out('fn hi\n out "hi"\n.\nhi()\nout hi()') == ["hi", "hi", "none"]


def test_functions_update_globals_but_inputs_are_local():
    src = """
let score 0
fn win points
    up score points
    let temp 1
.
win(5)
out score
"""
    assert out(src) == ["5"]
    with pytest.raises(RuntimeProblem):
        out(src + "out temp")


def test_closures():
    src = """
fn make
    let count 0
    fn inc
        up count
        ret count
    .
    ret inc
.
let counter make()
counter()
out counter()
"""
    assert out(src) == ["2"]


def test_builtins():
    assert out('out upper("hi"), round(2.5), round(3.14159, 2), sqrt(16), pow(2, 10)') == \
        ["HI 3 3.14 4 1024"]
    assert out('out split("a,b", ","), join(["a", "b"], "-"), rev("abc"), num("4.0"), txt(5)') == \
        ['["a", "b"] a-b cba 4 5']
    assert out("let r rand(1, 6)\nout r >= 1 and r <= 6") == ["true"]
    assert out('out type(1), type("a"), type(true), type([]), type(none), type(len)') == \
        ["number text bool list none fn"]


# ---------------------------------------------------------------- friendly errors
@pytest.mark.parametrize("source, words", [
    ('say "hi"', "'out'"),
    ('print "hi"', "'out'"),
    ("set x to 5", "'let'"),
    ("x = 5", "let x 5"),
    ("if x > 1", "'when'"),
    ("repeat 3", "'loop'"),
    ("when true\n out 1\nend", "just a dot"),
    ('out "hi', "never closed"),
    ("loop 3\nout 1", "never closed"),
    (".", "no block to close"),
    ("stop", "inside a 'loop'"),
    ("ret 1", "inside an 'fn'"),
    ("out 1 < 2 < 3", "two things at a time"),
    ("when true out 1", "next line"),
    ("let loop 1", "SimpleTalk word"),
    ("out 5 % 2", "mod"),
    ("# note", ";;"),
    ("let x", "needs a value"),
    ("out", None),
    ("score", "doesn't tell me to do anything"),
    ("fn f(a)\n.", "without brackets"),
    ("fn f a, b\n.", "spaces, not commas"),
    ("let l [1]\nout l [1]", "Remove the space"),
    ("when true\n out 1\n. out", "alone on its line"),
])
def test_syntax_errors_are_friendly(source, words):
    if words is None:
        out(source)           # valid program, nothing to check
        return
    err = problem(source, SyntaxProblem)
    assert words in str(err) or words in (err.hint or "")
    assert err.line is not None


@pytest.mark.parametrize("source, words", [
    ("out nmae", "I don't know what 'nmae' is"),
    ("let name 1\nout nmae", "Did you mean 'name'"),
    ("out length([1])", "use 'len'"),
    ("out area(3)", "fn area"),
    ("out [1][0]", "start at 1"),
    ("out [1][5]", "outside the list"),
    ("out 1 / 0", "divide by zero"),
    ('out "a" - 1', "num(...)"),
    ("when 5\n out 1\n.", "true or false"),
    ("let x 1\nadd x 2", "up x 2"),
    ("let l [1]\ndel l 9", "not in the list"),
    ("fn f a\n ret a\n.\nout f(1, 2)", "needs 1 value"),
    ("fn f\n ret f()\n.\nout f()", "calling itself"),
    ("out len(5)", "text or lists"),
    ('out 1 < "a"', "can't compare"),
    ("up y", "doesn't exist yet"),
    ("loop [1, 2]\n.", "loop item my_list"),
    ("out 1..100000000", "too big"),
    ('out 5 has 1', "'has' needs"),
])
def test_runtime_errors_are_friendly(source, words):
    err = problem(source, RuntimeProblem)
    assert words in str(err) or words in (err.hint or "")
    assert err.line is not None


def test_error_points_at_the_right_line():
    src = 'out "ok"\n\nout oops'
    err = problem(src, RuntimeProblem)
    assert err.line == 3
    text = err.pretty(src)
    assert "3 | out oops" in text and "^" in text


def test_windows_line_endings():
    assert out('out "a"\r\nout "b"\r\n') == ["a", "b"]


# ---------------------------------------------------------------- examples and CLI
@pytest.mark.parametrize("path", sorted(p for p in EXAMPLES.glob("*.simp") if "guess" not in p.name and "superpowers" not in p.name))
def test_examples_run(path, capsys):
    assert main([str(path)]) == 0
    assert "Oops" not in capsys.readouterr().err


def test_guessing_game(capsys, monkeypatch):
    import random
    random.seed(0)
    secret = random.randint(1, 20)
    random.seed(0)
    answers = iter(["abc", "25", str(secret)])
    monkeypatch.setattr("builtins.input", lambda prompt="": next(answers))
    assert main([str(EXAMPLES / "07_guess_the_number.simp")]) == 0
    printed = capsys.readouterr().out
    assert "Please type a number" in printed and "Stay between" in printed
    assert "Correct! You got it in 1 tries." in printed


def test_cli_missing_file_and_check(tmp_path, capsys):
    assert main([str(tmp_path / "nope.simp")]) == 2
    bad = tmp_path / "bad.simp"
    bad.write_text("out nmae\nlet x\n")
    assert main(["--check", str(bad)]) == 1
    assert "line 2" in capsys.readouterr().err


# ---------------------------------------------------------------- 2.1 features
def test_watch_reports_changes():
    lines = out("let s 1\nwatch s\nup s 2\nlet s s * 2\nlet l [1]\nwatch l\nadd l 5\nlet l[1] 9")
    assert lines == [
        "[watch] line 2: watching s, now 1",
        "[watch] line 3: s = 3  (was 1)",
        "[watch] line 4: s = 6  (was 3)",
        "[watch] line 6: watching l, now [1]",
        "[watch] line 7: l = [1, 5]",
        "[watch] line 8: l = [9, 5]",
    ]


def test_watch_loop_variable_and_unset_name():
    assert out("watch i\nloop i 1..2\n.") == [
        "[watch] line 1: watching i (not set yet)",
        "[watch] line 2: i = 1",
        "[watch] line 2: i = 2  (was 1)",
    ]


def test_tests_pass_and_fail_with_both_sides():
    from simpletalk import Interpreter, parse
    interp = Interpreter(output=lambda s: None)
    interp.run(parse("test 2 + 2 = 4\ntest [1, 2] has 2\ntest not false"))
    assert interp.tests_passed == 3
    err = problem("fn sq n\n ret n * 2\n.\ntest sq(3) = 9  ;; note", RuntimeProblem)
    assert "Test failed: sq(3) = 9" in str(err)
    assert "left side is 6" in err.hint and "right side is 9" in err.hint
    assert "true or false" in str(problem("test 5", RuntimeProblem))


def test_smart_input_keeps_asking():
    assert out('in a num "Age?"\nout a + 1', ["abc", "", "41"]) == \
        ["Please type a number.", "Please type a number.", "42"]
    assert out('in ok yes "Sure?"\nout ok', ["maybe", "YES"]) == ["Please answer yes or no.", "true"]
    assert out("in ok yes\nout ok", ["n"]) == ["false"]
    # `num` / `yes` right after the name always mean the answer type
    assert out("in a num\nout a * 2", ["x", "4"]) == ["Please type a number.", "8"]


def test_smart_input_without_answer_stops_cleanly():
    def no_input(prompt):
        raise EOFError
    with pytest.raises(RuntimeProblem) as info:
        run('in a num "Age?"', output=lambda s: None, input_fn=no_input)
    assert "no answer" in str(info.value)


def test_explain_reads_program_in_english():
    from simpletalk import parse
    from simpletalk.explain import explain
    text = explain(parse('let x 5\nwhen x > 3\n out "big"\nelse\n out "small"\n.\nloop i 1..3\n up x -1\n.'))
    assert "Store 5 in x." in text
    assert "If x is greater than 3:" in text and "Otherwise:" in text
    assert "Count i from 1 to 3, and each time:" in text
    assert "Take 1 away from x." in text


def test_explain_every_example(capsys):
    for path in sorted(EXAMPLES.glob("*.simp")):
        assert main(["--explain", str(path)]) == 0
    assert "Oops" not in capsys.readouterr().err


def test_trace_shows_each_line(tmp_path, capsys):
    f = tmp_path / "t.simp"
    f.write_text('let a 1\nout a\n')
    assert main(["--trace", str(f)]) == 0
    printed = capsys.readouterr().out.splitlines()
    assert printed == ["  > line 1   | let a 1", "  > line 2   | out a", "1"]


def test_cli_test_summary(tmp_path, capsys):
    f = tmp_path / "t.simp"
    f.write_text("test 1 = 1\ntest 2 = 2\n")
    assert main([str(f)]) == 0
    assert "[test] 2 tests passed." in capsys.readouterr().out
