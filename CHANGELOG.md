# Changelog

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
