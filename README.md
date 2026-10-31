<p align="center">
  <img src="assets/banner.png" alt="SimpleTalk – a tiny programming language for people learning to code" width="100%">
</p>

<p align="center">
  <a href="https://github.com/bicky21/SimpleTalk/actions/workflows/tests.yml"><img src="https://github.com/bicky21/SimpleTalk/actions/workflows/tests.yml/badge.svg" alt="Tests"></a>
  <img src="https://img.shields.io/badge/version-2.1.0-1C2A52" alt="Version 2.1.0">
  <img src="https://img.shields.io/badge/python-3.10%2B-2F67B1" alt="Python 3.10+">
  <img src="https://img.shields.io/badge/dependencies-none-66728C" alt="No dependencies">
</p>

<p align="center">
  <a href="#quick-start">Quick start</a> ·
  <a href="#what-makes-simpletalk-different">What's different</a> ·
  <a href="#the-language-in-one-minute">The language</a> ·
  <a href="docs/LANGUAGE.md">Full guide</a> ·
  <a href="examples">Examples</a>
</p>

---

SimpleTalk is a small programming language for people writing their first programs. It uses **24 short words**, closes every block with **a single dot**, and when something goes wrong it shows **where, why, and how to fix it**. It runs on plain Python with nothing else to install.

```
fn square n
    ret n * n
.

test square(4) = 16

loop i 1..5
    out "{i} squared is {square(i)}"
.
```

## Quick start

```bash
git clone https://github.com/bicky21/SimpleTalk.git
cd SimpleTalk
python3 -m venv .venv && source .venv/bin/activate
pip install -e .

simpletalk examples/01_hello.simp      # run a program
simpletalk                             # open the playground
```

On Windows, activate the environment with `.venv\Scripts\activate`. To skip installing, run `python3 -m simpletalk <file>` from the project folder.

## What makes SimpleTalk different

Most languages leave learning tools to separate programs: debuggers, test frameworks, linters. SimpleTalk builds them into the language, so they work from the very first line, with no setup and nothing new to learn.

### 1. It explains your code back to you

`--explain` reads a program and describes every line in plain English, without running it. Use it to check a program says what you meant.

```text
$ simpletalk --explain examples/03_decisions.simp
What examples/03_decisions.simp does:

   2  Store 72 in marks.
   4  If marks is at least 90:
   5      Show "Grade A"
      Otherwise, if marks is at least 70:
   7      Show "Grade B"
      Otherwise, if marks is at least 50:
   9      Show "Grade C"
      Otherwise:
  11      Show "Try again next time"
  14  If marks is greater than 40 and marks is not equal to 100:
  15      Show "You passed, and there is still room to grow."
```

### 2. Variables can report their own changes

`watch` tells you every time a variable changes, along with the line that changed it and the old value. You don't need to scatter print statements around.

```
let score 0
watch score
loop round 1..3
    up score round * 10
.
```
```text
[watch] line 2: watching score, now 0
[watch] line 4: score = 10  (was 0)
[watch] line 4: score = 30  (was 10)
[watch] line 4: score = 60  (was 30)
```

### 3. Tests are part of the language

Write `test` next to your code. When a test fails, it shows both sides, so you see the actual value straight away.

```
fn square n
    ret n * 2          ;; a bug
.
test square(3) = 9
```
```text
Oops! Something went wrong while running on line 4:

    4 | test square(3) = 9
        ^

  Test failed: square(3) = 9
  Hint: The left side is 6 and the right side is 9.
```

When every test passes, you get a one-line summary: `[test] 3 tests passed.`

### 4. Input that checks itself

`in age num` keeps asking until a number is typed, and `in ok yes` until the answer is yes or no (stored as `true` or `false`). That removes a whole class of beginner crashes.

```
in age num "How old are you?"
in likes yes "Do you like coding?"
```
```text
How old are you? twenty
Please type a number.
How old are you? 20
Do you like coding? maybe
Please answer yes or no.
```

### 5. Step-by-step runs

`--trace` shows each line just before it runs, so you can follow the order your program actually takes through loops and decisions.

```text
$ simpletalk --trace examples/02_variables.simp
  > line 2   | let name "Bicky"
  > line 3   | let age 20
  > line 4   | out "Hi {name}, you are {age} years old."
Hi Bicky, you are 20 years old.
```

### 6. Errors that teach

Every error points at the exact spot and suggests a fix. It catches spelling slips, and if you type a word from Python or another language, it tells you the SimpleTalk word to use instead.

```text
    2 | out "Hi {nmae}"
                 ^
  I don't know what 'nmae' is.
  Hint: Did you mean 'name'?
```
```text
    1 | print "hi"
        ^
  SimpleTalk doesn't use 'print'. The word for that is 'out'.
```

## The language in one minute

| To…                       | Write                                      |
|---------------------------|--------------------------------------------|
| Show something            | `out "Hello"`                              |
| Store a value             | `let age 12`                               |
| Add to a number           | `up age` adds 1, `up age 5` adds 5         |
| Ask the user              | `in name "Your name?"`                     |
| Decide                    | `when age > 10` … `else when` … `else` … `.` |
| Repeat                    | `loop 3` … `.`                             |
| Count                     | `loop i 1..10` … `.` (`10..1` counts down) |
| Go through a list         | `loop x my_list` … `.`                     |
| Repeat while              | `loop while x < 10` … `.`                  |
| Make a list               | `let fruits ["apple", "mango"]`            |
| Change a list             | `add fruits "kiwi"`, `del fruits "kiwi"`   |
| Check a list              | `fruits has "kiwi"`                        |
| Make a function           | `fn greet name` … `ret` … `.`              |
| Watch a variable          | `watch score`                              |
| Check your code           | `test score = 10`                          |
| Comment                   | `;; a note`                                |

That's nearly the whole language. The [full guide](docs/LANGUAGE.md) covers every keyword and built-in function, and includes a table for moving over from Python.

## Examples

| Program | Shows |
|---|---|
| [01_hello](examples/01_hello.simp) | Your first line |
| [02_variables](examples/02_variables.simp) | `let`, `up`, text with `{values}` |
| [03_decisions](examples/03_decisions.simp) | `when` / `else when` / `else` |
| [04_loops](examples/04_loops.simp) | Counting, ranges, `loop while`, `skip` |
| [05_lists](examples/05_lists.simp) | `add`, `del`, positions, `has` |
| [06_functions](examples/06_functions.simp) | `fn`, `ret`, recursion |
| [07_guess_the_number](examples/07_guess_the_number.simp) | A complete little game |
| [08_fizzbuzz](examples/08_fizzbuzz.simp) | The classic exercise |
| [09_superpowers](examples/09_superpowers.simp) | `watch`, `test` and smart input |

## Built to be stable

- **No raw Python errors.** Every problem becomes a SimpleTalk message. The interpreter is fuzz-tested with tens of thousands of random programs.
- **Guard rails.** Runaway recursion, endless input and huge ranges all stop with a clear explanation instead of freezing.
- **Locked-in behaviour.** A test suite covers the language, the examples and the error messages, and runs on Linux and Windows for every push.
- **Compatibility promise.** Within 2.x, working programs keep working. See the [changelog](CHANGELOG.md).

## Use it from Python

```python
from simpletalk import run
run('out "Hello from Python!"')
```

## How it works

```
simpletalk/
  lexer.py        text   → tokens
  parser.py       tokens → syntax tree, with friendly syntax errors
  interpreter.py  runs the tree: watch, test, smart input, runtime errors
  explain.py      syntax tree → plain English (--explain)
  builtins.py     len, sort, rand, … (23 functions)
  cli.py          the simpletalk command and playground
```

Contributions are welcome. Run `pip install -e ".[dev]"` and `python -m pytest` before opening a pull request.
