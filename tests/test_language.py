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
    ("out len(5)", "text, lists or maps"),
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
    src = 'out "ok"\n\nout whoops'
    err = problem(src, RuntimeProblem)
    assert err.line == 3
    text = err.pretty(src)
    assert "3 | out whoops" in text and "^" in text


def test_windows_line_endings():
    assert out('out "a"\r\nout "b"\r\n') == ["a", "b"]


# ---------------------------------------------------------------- examples and CLI
@pytest.mark.parametrize("name", sorted(p.name for p in EXAMPLES.glob("*.simp")
                                         if "guess" not in p.name and "superpowers" not in p.name))
def test_examples_run(name, tmp_path, capsys):
    import shutil
    work = tmp_path / "examples"
    shutil.copytree(EXAMPLES, work)        # examples may write files; keep the repo clean
    assert main([str(work / name)]) == 0
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


# ---------------------------------------------------------------- stability on small stacks
def test_deep_recursion_is_friendly_even_on_a_small_stack():
    """Windows gives Python ~1 MB of stack; Python 3.10 used to crash there."""
    import threading
    result = {}

    def job():
        try:
            out("fn f\n ret f()\n.\nout f()")
        except RuntimeProblem as err:
            result["message"] = err.message
        result["fact"] = out("fn fact n\n when n <= 1\n  ret 1\n .\n ret n * fact(n - 1)\n.\n"
                             "out len(txt(fact(900)))")

    old = threading.stack_size()
    threading.stack_size(1024 * 1024)
    try:
        t = threading.Thread(target=job)
        t.start()
    finally:
        threading.stack_size(old)
    t.join()
    assert "more than 1000 deep" in result["message"]
    assert result["fact"] == ["2270"]



# ---------------------------------------------------------------- 2.2: maps
def test_maps():
    src = """
let me {name: "Bicky", age: 20, "fav food": "momo"}
out me.name, me["fav food"], len(me), me has "age", me has "zip"
let me.age 21
let me["city"] "Kolkata"
del me "fav food"
out me
loop k me
    out k
.
out keys({a: 1, b: 2}), values({a: 1, b: 2}), {} = {}, {a: [1]} = {a: [1]}
"""
    assert out(src) == ['Bicky momo 3 true false', '{name: "Bicky", age: 21, city: "Kolkata"}',
                        "name", "age", "city", '["a", "b"] [1, 2] true true']


def test_nested_maps_and_lists():
    assert out('let s {tags: ["a"], inner: {x: 1}}\nadd s.tags "b"\nlet s.inner.x 2\nout s') == \
        ['{tags: ["a", "b"], inner: {x: 2}}']


def test_dot_still_closes_blocks():
    assert out('let m {a: 1}\nwhen m.a = 1\n out "yes"\n.') == ["yes"]


@pytest.mark.parametrize("source, words", [
    ('let me {name: "A"}\nout me.nmae', "Did you mean 'name'"),
    ("let l [1]\nout l.name", "Lists use positions"),
    ("let m {a: 1}\nout m[1]", "Map keys are text"),
    ('let m {a: 1}\nadd m 2', "give the key a value"),
    ('let m {a: 1}\ndel m "b"', "no key 'b'"),
])
def test_map_errors(source, words):
    err = problem(source, RuntimeProblem)
    assert words in str(err) or words in (err.hint or "")


def test_map_syntax_errors():
    assert "twice" in str(problem("let m {a: 1, a: 2}"))
    assert "name or plain text" in str(problem("let m {1: 2}"))


# ---------------------------------------------------------------- 2.2: try / fail / oops
def test_try_fail_catches_problems():
    src = """
try
    out num("abc")
fail why
    out "caught:", why
.
try
    out "fine"
fail
    out "not run"
.
"""
    assert out(src) == ['caught: "abc" doesn\'t look like a number.', "fine"]


def test_oops_raises_and_can_be_caught():
    src = 'fn check n\n when n < 0\n  oops "negative: {n}"\n .\n ret n\n.\n'
    assert out(src + "try\n out check(-5)\nfail why\n out why\n.") == ["negative: -5"]
    err = problem(src + "out check(-1)", RuntimeProblem)
    assert err.message == "negative: -1" and "The program stopped" in str(err)


def test_try_does_not_swallow_stop_or_syntax():
    assert out("loop i 1..5\n try\n  when i = 3\n   stop\n  .\n fail\n .\n out i\n.") == ["1", "2"]
    assert "needs a 'fail' part" in str(problem("try\n out 1\n."))
    assert "inside a 'try'" in str(problem("fail x"))


# ---------------------------------------------------------------- 2.2: pick
def test_pick():
    src = """
loop v ["sat", 3, 9, -2]
    pick v
    is "sat", "sun"
        out "weekend"
    is 1..5
        out "small"
    is -1..-10
        out "negative-ish"
    else
        out "other"
    .
.
"""
    assert out(src) == ["weekend", "small", "other", "negative-ish"]
    assert out("pick 7\nis 1\n out 1\n.") == []          # no match, no else: nothing


def test_pick_errors():
    assert "starts with 'is'" in str(problem("pick 3\nout 1\n."))
    assert "use = instead of 'is'" in str(problem("when 1 is 1\n."))
    assert "inside a 'pick'" in str(problem("is 3"))


# ---------------------------------------------------------------- 2.2: pipelines and lambdas
def test_pipelines():
    assert out("out [70, 95, 40, 82] | only it > 50 | each it * 2 | sort") == ["[140, 164, 190]"]
    assert out('out "a,b" | split(",") | join("-")') == ["a-b"]
    assert out("out [3, 1] | sort | rev, [1, 2] | sum") == ["[3, 1] 3"]
    assert out('out "hi" | each upper(it)') == ['["H", "I"]']


def test_lambdas():
    assert out("let double fn n -> n * 2\nout double(21)") == ["42"]
    assert out("let plus fn a b -> a + b\nout plus(2, 3)") == ["5"]
    assert out("let k 10\nlet addk fn n -> n + k\nout [1, 2] | each addk(it)") == ["[11, 12]"]
    assert out("fn apply f x\n ret f(x)\n.\nout apply(fn n -> n * n, 7)") == ["49"]


def test_pipeline_errors():
    assert "works on lists" in str(problem("out 5 | each it", RuntimeProblem))
    assert "true or false" in str(problem("out [1] | only it", RuntimeProblem))
    assert "'only', 'each', or a function" in str(problem("out [1] | 5"))


# ---------------------------------------------------------------- 2.2: modules
def test_use_brings_in_names(tmp_path, capsys):
    (tmp_path / "lib").mkdir()
    (tmp_path / "lib" / "shapes.simp").write_text("let unit \"cm\"\nfn area w h\n ret w * h\n.\n")
    (tmp_path / "main.simp").write_text('use "lib/shapes"\nuse "lib/shapes.simp"\nout area(3, 4), unit\n')
    assert main([str(tmp_path / "main.simp")]) == 0
    assert capsys.readouterr().out == "12 cm\n"


def test_use_errors_point_at_the_right_file(tmp_path, capsys):
    (tmp_path / "bad.simp").write_text("fn f\n    ret 1 / 0\n.\n")
    (tmp_path / "main.simp").write_text('use "bad"\nout f()\n')
    assert main([str(tmp_path / "main.simp")]) == 1
    err = capsys.readouterr().err
    assert "line 2 of bad.simp" in err and "ret 1 / 0" in err


def test_use_missing_and_circular(tmp_path, capsys):
    (tmp_path / "a.simp").write_text('use "b"\n')
    (tmp_path / "b.simp").write_text('use "a"\n')
    (tmp_path / "m.simp").write_text('use "nope"\n')
    assert main([str(tmp_path / "a.simp")]) == 1
    assert "uses itself" in capsys.readouterr().err
    assert main([str(tmp_path / "m.simp")]) == 1
    assert "can't find the file 'nope'" in capsys.readouterr().err


# ---------------------------------------------------------------- 2.2: files and JSON
def test_files_and_json(tmp_path, capsys):
    prog = tmp_path / "f.simp"
    prog.write_text('write("a.txt", "hello")\nout read("a.txt"), exists("a.txt"), exists("zz")\n'
                    'save("d.json", {n: [1, 2.5, true, none], s: "x"})\nlet d load("d.json")\nout d\n')
    assert main([str(prog)]) == 0
    assert capsys.readouterr().out == 'hello true false\n{n: [1, 2.5, true, none], s: "x"}\n'
    assert (tmp_path / "a.txt").read_text() == "hello"


def test_file_errors():
    assert "can't find the file" in str(problem('out read("no/such/file.txt")', RuntimeProblem))
    assert "can't store a fn" in str(problem('save("x.json", fn n -> n)', RuntimeProblem))


# ---------------------------------------------------------------- 2.2: keep
def test_keep_remembers_between_runs(tmp_path, capsys):
    prog = tmp_path / "counter.simp"
    prog.write_text("keep visits 0\nup visits\nout visits\nkeep seen []\nadd seen visits\nout seen\n")
    for _ in range(3):
        assert main([str(prog)]) == 0
    assert capsys.readouterr().out.split("\n")[-3:-1] == ["3", "[1, 2, 3]"]
    assert (tmp_path / "counter.memory.json").exists()


def test_keep_without_a_file_just_works():
    assert out("keep x 5\nup x\nout x") == ["6"]


# ---------------------------------------------------------------- 2.2: tasks
def test_tasks_run_side_by_side_and_await():
    src = """
task slow
    wait(0.15)
    out "slow"
    ret 42
.
out "first"
out await slow
"""
    assert out(src) == ["first", "slow", "42"]


def test_tasks_finish_before_program_ends():
    assert out('task t\n wait(0.05)\n out "late"\n.\nout "end"') == ["end", "late"]


def test_task_errors():
    err = problem('task t\n oops "broke"\n.\nout "main"', RuntimeProblem)
    assert err.message == "broke"
    assert "not a task" in str(problem("let t 5\nawait t", RuntimeProblem))
    src = 'task t\n oops "broke"\n.\ntry\n await t\nfail why\n out "caught", why\n.'
    assert out(src) == ["caught broke"]


# ---------------------------------------------------------------- 2.2: explain covers everything
def test_explain_new_features():
    from simpletalk import parse
    from simpletalk.explain import explain
    text = explain(parse(
        'let m {a: 1}\nout m.a\ntry\n oops "x"\nfail why\n out why\n.\npick 3\nis 1..5\n out 1\n.\n'
        'out [1] | only it > 0\nlet f fn n -> n\nkeep k 0\ntask t\n wait(0)\n.\nawait t\nuse "lib"'))
    for phrase in ["a map with a = 1", "the a of m", "Try this:", "Stop with the problem message",
                   "between 1 and 5", "keeping only the items", "a quick function",
                   "Remember k between runs", "Start a task called t", "Wait for task t",
                   "Bring in everything from the file"]:
        assert phrase in text, phrase



def test_piping_output_into_a_closed_reader_is_quiet(tmp_path):
    import subprocess
    import sys
    prog = tmp_path / "many.simp"
    prog.write_text("loop i 1..100000\n    out i\n.\n")
    p = subprocess.Popen([sys.executable, "-m", "simpletalk", str(prog)],
                         stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                         cwd=str(pathlib.Path(__file__).parent.parent))
    p.stdout.readline()
    p.stdout.close()                 # like `| head -1`
    err = p.stderr.read().decode()
    p.wait(timeout=10)
    assert "Traceback" not in err and "BrokenPipe" not in err


# ---------------------------------------------------------------- 2.3: fast engine, playground
def test_compiled_engine_matches_slow_paths():
    # whole numbers take the fast path; decimals, text and errors take the shared slow path
    assert out("out 2 + 3, 2.5 + 1, \"a\" + 1, 7 - 2, 7 / 2, 7 mod 3, 3 = 3.0, \"a\" != \"b\"") == \
        ["5 3.5 a1 5 3.5 1 true true"]
    assert out("let x 5\nup x 2.5\nout x\nloop 2.0\n out 1\n.") == ["7.5", "1", "1"]
    err = problem("loop 2.5\n.", RuntimeProblem)
    assert "whole number" in err.message and err.line == 1


def test_compiled_code_is_reused_and_isolated():
    from simpletalk import Interpreter, parse
    prog = parse("let n 0\nloop 3\n up n\n.\nout n")
    a, b = [], []
    Interpreter(output=a.append).run(prog)
    Interpreter(output=b.append).run(prog)        # same tree, second interpreter
    assert a == b == ["3"]


def test_playground_bundle_has_engine_and_examples():
    import json
    import runpy
    root = pathlib.Path(__file__).parent.parent
    runpy.run_path(str(root / "playground" / "build.py"), run_name="__main__")
    bundle = json.loads((root / "_site" / "bundle.json").read_text(encoding="utf-8"))
    engine_files = {f"simpletalk/{p.name}" for p in (root / "simpletalk").glob("*.py")}
    assert set(bundle["engine"]) == engine_files
    assert any(e["file"] == "01_hello.simp" for e in bundle["examples"])
    assert "lib/geometry.simp" in bundle["library"]
    for name in ("index.html", "worker.js", "bundle.json"):
        assert (root / "_site" / name).exists()



def test_check_json_for_editors(tmp_path, capsys):
    import json
    bad = tmp_path / "bad.simp"
    bad.write_text("out 1\nlet x\n")
    good = tmp_path / "good.simp"
    good.write_text('out "hi"\n')
    assert main(["--check", "--json", str(bad)]) == 1
    result = json.loads(capsys.readouterr().out)
    assert result == {"ok": False, "line": 2, "column": 6, "message": "'let' needs a value to store.",
                      "hint": "Write it like: let score 10"}
    assert main(["--check", "--json", str(good)]) == 0
    assert json.loads(capsys.readouterr().out) == {"ok": True}
