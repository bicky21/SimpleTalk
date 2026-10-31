# SimpleTalk

**A friendly programming language that reads like English.** Built in Python, made for beginners, and kind when you make mistakes.

```
set name to "Bicky"
say "Hello, {name}!"

repeat 3 times
    say "SimpleTalk is easy!"
end repeat

define square(n)
    return n * n
end define

for i from 1 to 5
    say "{i} squared is {square(i)}"
end for
```

## Why SimpleTalk?

- **Easy to remember** – 34 English keywords, one way to do each thing. The whole language fits on one page: [docs/LANGUAGE.md](docs/LANGUAGE.md).
- **Friendly errors** – every mistake shows the line, points at it, and suggests a fix:

  ```
  Oops! Something went wrong while running on line 3 of game.simp:

      3 | say "Hi {nmae}"
                   ^

    I don't know what 'nmae' is.
    Hint: Did you mean 'name'?
  ```
- **Stable** – no Python crashes leak through, a test suite locks in the behaviour, and 1.x releases never break working programs.
- **No setup** – pure Python 3.10+, no dependencies.

## Install and run

```bash
git clone https://github.com/bicky21/SimpleTalk.git
cd SimpleTalk
pip install -e .                    # gives you the `simpletalk` command

simpletalk examples/01_hello.simp   # run a program
simpletalk --check my_program.simp  # only check for mistakes
simpletalk                          # interactive playground
```

No install? This works too: `python -m simpletalk examples/01_hello.simp`

## A 1-minute tour

| You want to…            | Write                                   |
|-------------------------|-----------------------------------------|
| show something          | `say "Hello"`                           |
| store a value           | `set age to 12`                         |
| add to a number         | `change age by 1`                       |
| ask the user            | `ask "Your name?" into name`            |
| decide                  | `if age > 10 then` … `else` … `end if`  |
| repeat                  | `repeat 3 times` … `end repeat`         |
| count                   | `for i from 1 to 10` … `end for`        |
| go through a list       | `for each x in my_list` … `end for`     |
| make a list             | `set fruits to ["apple", "banana"]`     |
| add to a list           | `add "cherry" to fruits`                |
| make a function         | `define greet(name)` … `end define`     |

See the [examples/](examples) folder for complete programs, including a number-guessing game and FizzBuzz.

## Use it from Python

```python
from simpletalk import run
run('say "Hello from Python!"')
```

## Project layout

```
simpletalk/
  lexer.py        text  -> tokens
  parser.py       tokens -> tree of nodes (with friendly syntax errors)
  interpreter.py  runs the tree (with friendly runtime errors)
  builtins.py     length(), sort(), random(), ...
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

Status: **1.0.0** – see [CHANGELOG.md](CHANGELOG.md).
