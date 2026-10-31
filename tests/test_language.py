"""Tests that lock in how SimpleTalk behaves, so it stays stable."""

import pathlib

import pytest

from simpletalk import RuntimeProblem, SyntaxProblem, run
from simpletalk.cli import main

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


# ---------------------------------------------------------------- basics
def test_say_text_and_many_values():
    assert out('say "Hello, World!"') == ["Hello, World!"]
    assert out('say "a", 1, true, nothing, [1, "x"]') == ['a 1 true nothing [1, "x"]']


def test_empty_lines_comments_and_case_insensitive_keywords():
    assert out('\n\n# comment\nSAY "hi"   # trailing\n\n') == ["hi"]


def test_text_interpolation_and_escapes():
    assert out('set n to 3\nsay "n={n}, double={n * 2}"') == ["n=3, double=6"]
    assert out('say "{{x}} \\"q\\""') == ['{x} "q"']
    assert out("say 'single quotes work'") == ["single quotes work"]


def test_numbers_look_friendly():
    assert out("say 7 / 2, 6 / 3, 0.1 + 0.2, 10 mod 3, -2 * 3") == ["3.5 2 0.3 1 -6"]
    assert out("say 1_000_000") == ["1000000"]


def test_text_plus_anything_joins():
    assert out('say "Age: " + 12') == ["Age: 12"]


def test_set_change_and_ask_converts_numbers():
    assert out("set x to 5\nchange x by -2\nsay x") == ["3"]
    assert out('ask "Age?" into a\nsay a + 1', ["41"]) == ["42"]
    assert out('ask "Name?" into n\nsay type(n)', ["Bicky"]) == ["text"]


# ---------------------------------------------------------------- decisions
def test_if_else_if_else():
    src = """
set x to {}
if x > 10 then
    say "big"
else if x > 5
    say "medium"
else
    say "small"
end if
"""
    assert out(src.format(20)) == ["big"]
    assert out(src.format(7)) == ["medium"]
    assert out(src.format(1)) == ["small"]


def test_is_and_is_not_and_logic():
    assert out('say 1 is 1, 1 is not 2, "a" = "a", not false, true and false, true or false') == \
        ["true true true true false true"]
    assert out("say 1 = 1.0, 1 = \"1\", 1 = true") == ["true false false"]


def test_short_circuit_logic():
    assert out("say false and (1 / 0 = 1)") == ["false"]


# ---------------------------------------------------------------- loops
def test_repeat_times_runs_exactly_n_times():
    assert out('repeat 3 times\n say "x"\nend repeat') == ["x"] * 3
    assert out('repeat 0 times\n say "x"\nend repeat') == []          # old bug: printed once


def test_nested_repeat():
    assert out('repeat 2 times\n repeat 3 times\n  say "x"\n end\nend') == ["x"] * 6


def test_repeat_while_until_forever_stop_skip():
    assert out("set i to 0\nrepeat while i < 3\n change i by 1\nend\nsay i") == ["3"]
    assert out("set i to 0\nrepeat until i = 4\n change i by 1\nend\nsay i") == ["4"]
    src = """
set i to 0
repeat forever
    change i by 1
    if i = 2
        skip
    end if
    if i > 4
        stop
    end if
    say i
end repeat
"""
    assert out(src) == ["1", "3", "4"]


def test_for_range_counts_up_and_down():
    assert out("for i from 1 to 3\n say i\nend for") == ["1", "2", "3"]
    assert out("for i from 3 to 1\n say i\nend") == ["3", "2", "1"]


def test_for_each_list_and_text():
    assert out('for each x in [1, "b"]\n say x\nend') == ["1", "b"]
    assert out('for each c in "hi"\n say c\nend') == ["h", "i"]


def test_changing_list_while_looping_is_safe():
    assert out("set l to [1, 2]\nfor each x in l\n add x to l\nend\nsay l") == ["[1, 2, 1, 2]"]


# ---------------------------------------------------------------- lists
def test_lists_are_one_based_with_negative_from_end():
    assert out("set l to [10, 20, 30]\nsay l[1], l[-1], length(l)") == ["10 30 3"]
    assert out("set l to [1, 2]\nset l[2] to 9\nadd 3 to l\nremove 1 from l\nsay l") == ["[9, 3]"]
    assert out('say "b" in ["a", "b"], "ell" in "hello"') == ["true true"]


# ---------------------------------------------------------------- functions
def test_functions_return_and_recursion():
    src = """
define fact(n)
    if n <= 1
        return 1
    end if
    return n * fact(n - 1)
end define
say fact(10)
"""
    assert out(src) == ["3628800"]


def test_function_without_return_gives_nothing():
    assert out("define f()\n set a to 1\nend\nsay f()") == ["nothing"]


def test_functions_update_globals_but_params_are_local():
    src = """
set score to 0
define win(score_add)
    change score by score_add
    set temp to 1
end define
win(5)
say score
"""
    assert out(src) == ["5"]
    with pytest.raises(RuntimeProblem):
        out(src + "say temp")


def test_closures():
    src = """
define make()
    set count to 0
    define inc()
        change count by 1
        return count
    end
    return inc
end
set counter to make()
counter()
say counter()
"""
    assert out(src) == ["2"]


def test_builtins():
    assert out('say upper("hi"), round(2.5), round(3.14159, 2), sqrt(16), power(2, 10)') == \
        ["HI 3 3.14 4 1024"]
    assert out('say split("a,b", ","), join(["a", "b"], "-"), reverse("abc"), number("4.0")') == \
        ['["a", "b"] a-b cba 4']
    assert out("set r to random(1, 6)\nsay r >= 1 and r <= 6") == ["true"]


# ---------------------------------------------------------------- friendly errors
@pytest.mark.parametrize("source, words", [
    ("x = 5", "set x to"),
    ('say "hi', "never closed"),
    ("repeat 3 times\nsay 1", "never closed"),
    ("end", "nothing to close"),
    ("stop", "inside a loop"),
    ("return 1", "inside a 'define'"),
    ("say 1 < 2 < 3", "two things at a time"),
    ("if true then say 1", "next line"),
    ("set to to 1", "SimpleTalk word"),
    ("say 5 % 2", "mod"),
    ("repeat 2 times\nsay 1\nend if", "end repeat"),
    ("say", "needs something"),
    ("score", "doesn't tell me to do anything"),
])
def test_syntax_errors_are_friendly(source, words):
    err = problem(source, SyntaxProblem)
    assert words in str(err) or words in (err.hint or "")
    assert err.line is not None


@pytest.mark.parametrize("source, words", [
    ("say nmae", "I don't know what 'nmae' is"),
    ('print("hi")', "use 'say'"),
    ("say [1][0]", "start at 1"),
    ("say [1][5]", "outside the list"),
    ("say 1 / 0", "divide by zero"),
    ('say "a" - 1', "number(...)"),
    ("if 5\n say 1\nend", "true or false"),
    ("set x to 1\nadd 2 to x", "change x by 2"),
    ("set l to [1]\nremove 9 from l", "not in the list"),
    ("define f(a)\n return a\nend\nsay f(1, 2)", "needs 1 value"),
    ("define f()\n return f()\nend\nsay f()", "calling itself"),
    ('say length(5)', "text or lists"),
    ('say 1 < "a"', "can't compare"),
    ("change y by 1", "doesn't exist yet"),
])
def test_runtime_errors_are_friendly(source, words):
    err = problem(source, RuntimeProblem)
    assert words in str(err) or words in (err.hint or "")
    assert err.line is not None


def test_error_points_at_the_right_line():
    err = problem('say "ok"\n\nsay oops', RuntimeProblem)
    assert err.line == 3
    text = err.pretty('say "ok"\n\nsay oops')
    assert "3 | say oops" in text and "^" in text


def test_windows_line_endings():
    assert out('say "a"\r\nsay "b"\r\n') == ["a", "b"]


# ---------------------------------------------------------------- examples and CLI
@pytest.mark.parametrize("path", sorted(p for p in EXAMPLES.glob("*.simp") if "guess" not in p.name))
def test_examples_run(path, capsys):
    assert main([str(path)]) == 0
    assert "Oops" not in capsys.readouterr().err


def test_cli_missing_file_and_check(tmp_path, capsys):
    assert main([str(tmp_path / "nope.simp")]) == 2
    bad = tmp_path / "bad.simp"
    bad.write_text("say nmae\nset x to\n")
    assert main(["--check", str(bad)]) == 1
    assert "line 2" in capsys.readouterr().err
