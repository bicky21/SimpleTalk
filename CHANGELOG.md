# Changelog

## 2.3.1 – 2026-10-31

### Added
- VS Code extension 2.3.1: Run with F5 or the ▶ button, Explain and Trace commands,
  mistakes underlined in red on save, finds the project's `.venv` automatically.
- `simpletalk --check --json file.simp` prints the result as JSON, for editors.

## 2.3.0 – 2026-10-31

Faster, and easier to start with.

### Added
- **Online playground** (`playground/`, published with GitHub Pages): runs the real engine in the
  browser through Pyodide in a Web Worker. Examples menu, Explain, answers for `in`, Stop for
  runaway programs, shareable links, `keep` remembered in the browser, light and dark themes,
  works on phones. `?pyodide=/path/` loads the engine from your own server (for offline classrooms).
- **VS Code extension** (`editors/vscode/`): highlighting, snippets, auto-indent, `;;` comment toggling.
- `benchmarks/` with two programs used to measure speed.

### Changed
- **Faster engine** (`compiler.py`): programs are compiled to Python closures before running,
  4–5× faster on loops and calls. Identical output and error messages, checked by running
  8,607 random programs through the old and new engines.

## 2.2.0 – 2026-10-31

Advanced features, still pure Python with no dependencies.

### Added
- Maps: `{name: "Bicky", age: 20}`, `me.name`, `me["key"]`, `let me.age 21`, `del me "age"`, `has`, `keys()`, `values()`.
- Pipelines: `list | only it > 1 | each it * 2 | sort`, with any function as a step.
- Quick functions: `fn n -> n * 2`, which can be stored and passed to other functions.
- Pattern matching: `pick value` / `is a, b` / `is 1..5` / `else`.
- Error handling: `try` ... `fail why` ... `.`, and `oops "message"` to raise your own problem.
- Modules: `use "lib/file"`, relative to the program, with errors reported in the right file.
- Files and JSON: `read`, `write`, `load`, `save`, `exists`.
- Remembered values: `keep name default` saves to `<program>.memory.json` between runs.
- Tasks: `task name` ... `.` runs alongside the program; `await name` waits and returns its result.
- Examples 10–15.

### Fixed
- Windows + Python 3.10 crashed on deep recursion (the failing CI badge). Programs now run on a
  large-stack worker thread, and Ctrl+C stops cleanly, even while waiting for input.
- `wait()` can now be interrupted with Ctrl+C.

### Changed
- New keywords (so they can't be variable names): `try`, `fail`, `oops`, `pick`, `is`, `use`, `keep`, `task`, `await`.
- `len()` also counts the entries of a map.

## 2.1.0 – 2026-10-31

Learning tools built into the language.

### Added
- `watch name`: report every change to a variable (line number, new and old value), including lists changed in place.
- `test check`: tests inside your program. A failure shows both sides; a summary is printed when all pass.
- Smart input: `in age num "Age?"` asks again until a number is typed; `in ok yes "Sure?"` until yes or no (stored as true/false).
- `simpletalk --explain file.simp`: describes the program line by line in plain English.
- `simpletalk --trace file.simp`: shows each line just before it runs.
- `examples/09_superpowers.simp`, banner image, rewritten README.

### Changed
- `watch` and `test` are now keywords (24 in total), so they can no longer be used as variable names.
- If input ends while `in ... num` / `in ... yes` is waiting, the program stops with a clear message instead of asking forever.

## 2.0.0 – 2026-10-31

New, shorter syntax. **Breaking:** 1.0 programs need to be rewritten (see the table in docs/LANGUAGE.md).
When you type a 1.0 or Python word, SimpleTalk tells you the 2.0 word to use.

### Changed
- Keywords are now short (22 in total, 2–5 letters): `let`, `up`, `out`, `in`, `add`, `del`, `when`, `else`,
  `loop`, `while`, `stop`, `skip`, `fn`, `ret`, `and`, `or`, `not`, `has`, `mod`, `true`, `false`, `none`.
- Blocks end with a line containing just a dot (`.`) instead of `end`.
- One `loop` keyword replaces `repeat` / `for`: `loop 3`, `loop i 1..10`, `loop x list`, `loop while ...`, `loop`.
- `fn name a b` defines functions (inputs separated by spaces); `ret` gives back a value.
- `add list value` / `del list value`; `list has value` replaces `value in list`.
- Comments start with `;;`. Keywords are lowercase only.
- Built-ins renamed to short names: `len`, `num`, `isnum`, `txt`, `pow`, `rand`, `swap`, `rev`.
- `type()` returns `"bool"`, `"none"` and `"fn"`; `none` replaces `nothing`.

### Added
- Ranges: `1..5` (counts down with `5..1`). Loops over ranges don't build a list in memory.
- `up x` with no amount adds 1. `in name` works without a question.
- Spacing rule: `f(x)` / `list[1]` with no space before the bracket call or pick an item.
- Guess-the-number example checks the 1–20 range.


## 1.0.0 – 2026-10-31

First stable release. The interpreter was rewritten from scratch.

### Fixed (bugs in the old 0.1 interpreters)
- `say "Hello, World!"` printed an error: text was split on spaces, so any message with a space broke.
- An empty line crashed the program (`IndexError`).
- `repeat 0 times` still ran the block once.
- A bare `end` crashed the program (`IndexError`).
- The program file name was hard-coded (`hello.simp` / `repeat.simp`) and `program/hello.simp` was never found.
- Bad numbers in `repeat` crashed with a Python `ValueError`.

### Added
- Real lexer → parser → interpreter design.
- Variables (`set`, `change`), input (`ask ... into`), text interpolation (`"Hi {name}"`).
- `if / else if / else`, `repeat N times / while / until / forever`, `for ... from ... to`, `for each`, `stop`, `skip`.
- Lists with 1-based positions, `add`, `remove`, `in`.
- Functions with `define`, `return`, recursion and closures.
- 23 built-in functions.
- Friendly errors with line numbers, a `^` marker, and hints (including "Did you mean ...?" and Python-to-SimpleTalk tips).
- `simpletalk` command: run files, `--check`, `--version`, and an interactive playground.
- Test suite and GitHub Actions CI.

### Removed
- Committed PyInstaller output (`build/`, `dist/`, about 40 MB of Windows binaries) and the unrelated C/C++ VS Code task.
