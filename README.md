# SimpleTalk

**A tiny, friendly programming language.** Short words, no clutter, and kind error messages. Built in Python.

```
let name "Bicky"
out "Hello, {name}!"

loop 3
    out "SimpleTalk is easy!"
.

fn square n
    ret n * n
.

loop i 1..5
    out "{i} squared is {square(i)}"
.
```

## Why SimpleTalk?

- **Type less** – 22 keywords, each 2–5 letters (`let`, `out`, `when`, `loop`, `fn`). No colons, no braces, no `end`: a block simply ends with a `.` line.
- **Easy to remember** – one way to do each thing. The whole language fits on one page: [docs/LANGUAGE.md](docs/LANGUAGE.md).
- **Friendly errors** – every mistake shows the line, points at it, and suggests a fix:

  ```
  Oops! I could not understand the code on line 2 of game.simp:

      2 | print "hi"
          ^

    SimpleTalk doesn't use 'print'. The word for that is 'out'.
  ```
- **Stable** – no Python crashes leak through (fuzz-tested), a test suite locks in the behaviour, and 2.x releases never break working programs.
- **No setup** – pure Python 3.10+, no dependencies.

## Install and run

```bash
git clone https://github.com/bicky21/SimpleTalk.git
cd SimpleTalk
python3 -m venv .venv               # Ubuntu/Debian need a virtual environment
source .venv/bin/activate
pip install -e .                    # gives you the `simpletalk` command

simpletalk examples/01_hello.simp   # run a program
simpletalk --check my_program.simp  # only check for mistakes
simpletalk                          # interactive playground
```

No install? This works too: `python3 -m simpletalk examples/01_hello.simp`

## The whole language at a glance

| You want to…            | Write                                   |
|-------------------------|-----------------------------------------|
| show something          | `out "Hello"`                           |
| store a value           | `let age 12`                            |
| add to a number         | `up age` (adds 1) or `up age 5`         |
| ask the user            | `in name "Your name?"`                  |
| decide                  | `when age > 10` … `else` … `.`          |
| repeat                  | `loop 3` … `.`                          |
| count                   | `loop i 1..10` … `.`                    |
| go through a list       | `loop x my_list` … `.`                  |
| repeat while            | `loop while x < 10` … `.`               |
| make a list             | `let fruits ["apple", "banana"]`        |
| add / delete in a list  | `add fruits "kiwi"` / `del fruits "kiwi"` |
| check a list            | `fruits has "kiwi"`                     |
| make a function         | `fn greet name` … `ret` … `.`           |
| comment                 | `;; a note`                             |

See [examples/](examples) for complete programs, including a number-guessing game and FizzBuzz.

## Use it from Python

```python
from simpletalk import run
run('out "Hello from Python!"')
```

## Project layout

```
simpletalk/
  lexer.py        text  -> tokens
  parser.py       tokens -> tree of nodes (with friendly syntax errors)
  interpreter.py  runs the tree (with friendly runtime errors)
  builtins.py     len(), sort(), rand(), ...
  values.py       how values are shown and compared
  errors.py       the "Oops!" messages
  cli.py          the `simpletalk` command and playground
examples/         sample programs
tests/            pytest suite (run: python -m pytest)
docs/LANGUAGE.md  the full language guide
```

## Development

```bash
pip install -e ".[dev]"
python -m pytest
```

Status: **2.0.0** – see [CHANGELOG.md](CHANGELOG.md).
