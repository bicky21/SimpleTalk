# Changelog

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
