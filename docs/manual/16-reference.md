# Reference

Everything in SimpleTalk on one page. Version 2.3.

## Layout

- One instruction per line. Indentation is optional.
- Blocks (`when`, `loop`, `fn`, `try`, `pick`, `task`) end with a line holding just `.`.
- `;;` starts a comment.
- No space before `(` or `[` when calling a function or picking an item: `area(3, 4)`, `list[1]`, `me.name`.
- Inside `( )`, `[ ]` and `{ }`, a value may continue onto the next lines.

## All 33 keywords

| Keyword | Meaning | Example |
|---|---|---|
| `let` | store a value | `let age 20` |
| `up` | add to a number (default 1) | `up age`, `up age -2` |
| `out` | show values | `out "Hi", name` |
| `in` | ask a question | `in name "Name?"`, `in age num "Age?"`, `in ok yes "Sure?"` |
| `add` | put an item at the end of a list | `add items "kiwi"` |
| `del` | remove an item from a list, or a key from a map | `del items "kiwi"` |
| `when` / `else` | decide | `when x > 1` … `else when` … `else` … `.` |
| `loop` | repeat | `loop 3`, `loop i 1..5`, `loop x items`, `loop` |
| `while` | after `loop`: repeat while true | `loop while x < 10` |
| `stop` / `skip` | leave the loop / go to the next round | |
| `fn` | make a function, or a quick function | `fn area w h` … `.`, `fn n -> n * 2` |
| `ret` | give back a value from a function or task | `ret w * h` |
| `try` / `fail` | catch problems | `try` … `fail why` … `.` |
| `oops` | stop with your own problem | `oops "Not enough money"` |
| `pick` / `is` | choose by value | `pick x` / `is 1, 2` / `is 5..9` / `else` / `.` |
| `use` | bring in another file | `use "lib/geometry"` |
| `keep` | a variable remembered between runs | `keep best 0` |
| `task` / `await` | run side by side / wait for it | `task t` … `.`, `let r await t` |
| `watch` | report every change to a variable | `watch score` |
| `test` | check that something is true | `test square(3) = 9` |
| `and` `or` `not` | combine true/false | `x > 1 and x < 9` |
| `has` | list contains / text contains / map has key | `items has "kiwi"` |
| `mod` | remainder | `10 mod 3` |
| `true` `false` `none` | values | |

`only`, `each` and `it` have a special meaning in pipelines, but are not reserved. Keywords are always lowercase.

## Values

| Kind | Written as | `type(...)` |
|---|---|---|
| number | `42`, `-3.5`, `1_000` | `"number"` |
| text | `"hi"`, `'hi'`, `"Hi {name}"` | `"text"` |
| bool | `true`, `false` | `"bool"` |
| list | `[1, 2]`, `1..5` | `"list"` |
| map | `{name: "A", "two words": 2}` | `"map"` |
| none | `none` | `"none"` |
| function | `fn ...`, `len` | `"fn"` |
| task | `task ...` | `"task"` |

Text escapes: `\n` new line, `\t` tab, `\"` and `\'` quotes, `\\` backslash, `{{` and `}}` real braces.

## Operators, from first to last

| Order | Operators | Notes |
|---|---|---|
| 1 | `( )`, `f(x)`, `x[i]`, `m.key` | |
| 2 | `-x` | negative |
| 3 | `*` `/` `mod` | `7 / 2` is `3.5` |
| 4 | `+` `-` | text `+` anything joins text; list `+` list joins lists |
| 5 | `a..b` | range, counts down when b < a |
| 6 | `=` `!=` `<` `>` `<=` `>=` `has` | one comparison at a time |
| 7 | `not` | |
| 8 | `and` | stops early when the left side is false |
| 9 | `or` | stops early when the left side is true |
| 10 | `\|` | pipeline steps: `only`, `each`, or a function |

```simp
out 2 + 3 * 4, (2 + 3) * 4, -2 * 3, 7 / 2, 7 mod 2
out (1..3) + [9], not 1 > 2 and 3 > 2
```

```output
14 20 -6 3.5 1
[1, 2, 3, 9] true
```

## Built-in functions

| Function | Gives back | Example → result |
|---|---|---|
| `len(x)` | number of letters, items or keys | `len("hello")` → `5` |
| `num(x)` | text as a number | `num("4.5")` → `4.5` |
| `isnum(x)` | can x be a number? | `isnum("abc")` → `false` |
| `txt(x)` | any value as text | `txt(42)` → `"42"` |
| `type(x)` | the kind of value | `type([])` → `"list"` |
| `round(x, digits)` | rounded (2.5 → 3) | `round(3.14159, 2)` → `3.14` |
| `abs(x)` | without the minus sign | `abs(-5)` → `5` |
| `sqrt(x)` | square root | `sqrt(16)` → `4` |
| `pow(x, y)` | x to the power y | `pow(2, 10)` → `1024` |
| `rand(a, b)` | a random whole number from a to b | `rand(1, 6)` → a dice roll |
| `min(...)`, `max(...)` | smallest, largest | `max(3, 9, 2)` → `9`, also `max(list)` |
| `sum(list)` | total | `sum([1, 2, 3])` → `6` |
| `upper(t)`, `lower(t)` | capitals, small letters | `upper("hi")` → `"HI"` |
| `trim(t)` | without spaces at the ends | `trim("  hi ")` → `"hi"` |
| `swap(t, old, new)` | text with old replaced by new | `swap("cat", "c", "b")` → `"bat"` |
| `split(t, sep)` | text cut into a list | `split("a,b", ",")` → `["a", "b"]` |
| `join(list, sep)` | list glued into text | `join(["a", "b"], "-")` → `"a-b"` |
| `sort(list)` | a sorted copy | `sort([3, 1, 2])` → `[1, 2, 3]` |
| `rev(x)` | a reversed copy of a list or text | `rev("abc")` → `"cba"` |
| `copy(list)` | a separate copy | |
| `keys(map)`, `values(map)` | lists of keys, values | `keys({a: 1})` → `["a"]` |
| `read(file)`, `write(file, text)` | text files | chapter 11 |
| `load(file)`, `save(file, value)` | JSON files | chapter 11 |
| `exists(file)` | does the file exist? | |
| `wait(seconds)` | pause | `wait(0.5)` |

```simp
out len("hello"), num("4.5"), isnum("abc"), txt(42) + "!", type([])
out round(3.14159, 2), round(2.5), abs(-5), sqrt(16), pow(2, 10)
out max(3, 9, 2), min([4, 1]), sum([1, 2, 3])
out upper("hi"), trim("  hi "), swap("cat", "c", "b")
out split("a,b", ","), join(["a", "b"], "-"), sort([3, 1, 2]), rev("abc")
out keys({a: 1, b: 2}), values({a: 1, b: 2})
```

```output
5 4.5 false 42! list
3.14 3 5 4 1024
9 1 6
HI hi bat
["a", "b"] a-b [1, 2, 3] cba
["a", "b"] [1, 2]
```

## The simpletalk command

| Command | Does |
|---|---|
| `simpletalk file.simp` | run a program |
| `simpletalk --explain file.simp` | describe it in plain English |
| `simpletalk --trace file.simp` | run it, showing each line first |
| `simpletalk --check file.simp` | look for mistakes without running |
| `simpletalk --check --json file.simp` | the same, as JSON (for editors) |
| `simpletalk` | interactive mode |
| `simpletalk --version` | which version is installed |

Exit codes: 0 means fine, 1 means the program had a problem, 2 means the file couldn't be read, and 130 means it was stopped with Ctrl+C.

## Limits

| Limit | Value |
|---|---|
| functions calling functions | 1000 deep |
| a range turned into a list | 10 million items (looping over a range has no limit) |
| output in the playground | 20,000 lines per run |

## Using SimpleTalk from Python

```python
from simpletalk import run
run('out "Hello from Python!"')
```
