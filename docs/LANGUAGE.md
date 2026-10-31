# The SimpleTalk Language Guide (version 2.0)

SimpleTalk is designed around three rules:

1. **Type less.** Every keyword is 2–5 letters: `let`, `out`, `when`, `loop`, `fn`.
2. **One way to do each thing.** Only **22 keywords** and **23 built-in functions** — this page lists all of them.
3. **Never crash with a scary error.** Every mistake gets a line number, a `^` marker and a hint.

---

## 1. The whole language on one card

```
;; comment
let name "Bicky"          ;; store a value
out "Hi {name}"           ;; show it
in age "Your age?"        ;; ask the user
up age                    ;; add 1   (up age 5 adds 5, up age -1 takes 1 away)

when age >= 18            ;; decide
    out "adult"
else when age >= 13
    out "teen"
else
    out "kid"
.                         ;; a dot closes the block

loop 3                    ;; 3 times
    out "hi"
.
loop i 1..5               ;; count 1 to 5
    out i
.
loop f ["apple", "kiwi"]  ;; every item of a list
    out f
.
loop while age < 21       ;; while something is true
    up age
.
loop                      ;; forever — leave with stop
    stop
.

fn area w h               ;; your own function
    ret w * h
.
out area(3, 4)
```

## 2. Two layout rules

1. **One instruction per line.** Indentation is optional, but it makes code easier to read.
2. **A block ends with a line holding just a dot (`.`).** `when`, `loop` and `fn` all start blocks.

And one spacing rule:

> **No space before `(` or `[` when calling or picking an item.**
> `area(3, 4)` calls a function and `fruits[1]` picks an item.
> With a space, `[1, 2]` and `(3 + 4)` are just values.

Keywords are lowercase. Names are case-sensitive: `score` and `Score` are different.

## 3. Values

| Kind   | Examples                    | Notes                                       |
|--------|-----------------------------|---------------------------------------------|
| number | `42`, `3.5`, `-7`, `1_000`  | `7 / 2` is `3.5`, `6 / 3` is `2`             |
| text   | `"hello"`, `'hi'`           | `{name}` inside text inserts a value        |
| bool   | `true`, `false`             | the answer to a question like `x > 3`       |
| list   | `[1, 2, 3]`, `[]`, `1..5`   | positions start at **1**                    |
| none   | `none`                      | "no value"                                  |
| fn     | `fn ...`, `len`             | something you can call with `( )`           |

### Text tricks
```
out "Hi {name}, 2 + 2 is {2 + 2}"   ;; Hi Bicky, 2 + 2 is 4
out "Use {{ and }} for real braces" ;; Use { and } for real braces
out "Line one\nLine two"            ;; \n new line, \t tab, \" quote
out "Age: " + 12                    ;; text + anything = joined text
```

## 4. Storing and changing values

```
let score 10            ;; create or replace
let score score * 2     ;; use the old value to make a new one
up score                ;; add 1
up score 5              ;; add 5
up score -5             ;; take 5 away
in name "Your name?"    ;; ask; a typed number becomes a real number
in answer               ;; ask without a question
```

## 5. Maths and comparisons

| Write         | Meaning                                    |
|---------------|--------------------------------------------|
| `+ - * /`     | add, subtract, multiply, divide            |
| `mod`         | remainder: `10 mod 3` is `1`               |
| `=`  `!=`     | equal, not equal                           |
| `< > <= >=`   | less / greater                             |
| `has`         | `fruits has "kiwi"`, `"hello" has "ell"`   |
| `and or not`  | combine true/false answers                 |
| `a..b`        | a range: `1..5` is `[1, 2, 3, 4, 5]`, `5..1` counts down |

Order: brackets, `-` (negative), `* / mod`, `+ -`, `..`, comparisons, `not`, `and`, `or`.

Compare two things at a time: write `x > 1 and x < 10`, not `1 < x < 10`.

## 6. Decisions

```
when marks >= 90
    out "A"
else when marks >= 70
    out "B"
else
    out "Keep going!"
.
```

One dot closes the whole `when` / `else when` / `else` chain.
The check must be `true` or `false` — SimpleTalk won't guess what `when 5` means.

## 7. Loops

| Write                 | Does                                         |
|-----------------------|----------------------------------------------|
| `loop 3`              | 3 times (any number or value: `loop n * 2`)  |
| `loop i 1..10`        | counts; `10..1` counts down                  |
| `loop x my_list`      | every item of a list (or letter of a text)   |
| `loop while x < 10`   | while something is true                      |
| `loop`                | forever, until `stop`                        |

Inside any loop, `stop` leaves the loop and `skip` jumps to the next round.

How SimpleTalk tells `loop 3` from `loop i 1..10`: if a name is followed by a value, it's the loop's name.

## 8. Lists

```
let shopping ["milk", "eggs"]
add shopping "bread"           ;; put at the end
del shopping "eggs"            ;; remove the first match
let shopping[1] "oat milk"     ;; change an item
out shopping[1]                ;; first item
out shopping[-1]               ;; last item
out len(shopping)              ;; how many items
when shopping has "bread"
    out "yes"
.
```

Positions start at **1**. `[0]` is an error with a helpful hint. Text works the same way: `"hello"[1]` is `"h"`.

## 9. Functions

```
fn greet name
    out "Hello, {name}!"
.

fn area width height
    ret width * height
.

fn hello                 ;; no inputs
    out "hi"
.

greet("Bicky")
out area(3, 4)
hello()
```

- Inputs are listed after the name, separated by spaces (no brackets, no commas).
- A function without `ret` gives back `none`.
- Inputs belong to the function. `let` inside a function changes an outer variable **if it already exists**; otherwise it makes one that only lives inside the function.
- Functions can call themselves up to 1000 levels deep.

## 10. Built-in functions

| Function                | Example                                 |
|-------------------------|-----------------------------------------|
| `len(x)`                | `len("hello")` → `5`                    |
| `num(x)`                | `num("42")` → `42`                      |
| `isnum(x)`              | `isnum("4.5")` → `true`                 |
| `txt(x)`                | `txt(42)` → `"42"`                      |
| `type(x)`               | `type([1])` → `"list"`                  |
| `round(x, digits)`      | `round(3.14159, 2)` → `3.14` (2.5 → 3)  |
| `abs(x)`                | `abs(-5)` → `5`                         |
| `sqrt(x)`               | `sqrt(16)` → `4`                        |
| `pow(x, y)`             | `pow(2, 10)` → `1024`                   |
| `rand(low, high)`       | `rand(1, 6)` → a whole number 1 to 6    |
| `min(...)` / `max(...)` | `max(3, 9, 2)` or `max(my_list)`        |
| `sum(list)`             | `sum([1, 2, 3])` → `6`                  |
| `upper(t)` / `lower(t)` | `upper("hi")` → `"HI"`                  |
| `trim(t)`               | `trim("  hi ")` → `"hi"`                |
| `swap(t, old, new)`     | `swap("cat", "c", "b")` → `"bat"`       |
| `split(t, sep)`         | `split("a,b", ",")` → `["a", "b"]`      |
| `join(list, sep)`       | `join(["a", "b"], "-")` → `"a-b"`       |
| `sort(list)`            | `sort([3, 1, 2])` → `[1, 2, 3]` (new list) |
| `rev(x)`                | `rev("abc")` → `"cba"` (new value)      |
| `copy(list)`            | a separate copy of a list               |
| `wait(seconds)`         | `wait(0.5)` pauses half a second        |

## 11. All 22 keywords

```
let up out in add del
when else loop while stop skip fn ret
and or not has mod true false none
```

These can't be used as variable names.

## 12. Coming from Python (or SimpleTalk 1.0)?

| Python                    | SimpleTalk 1.0            | SimpleTalk 2.0        |
|---------------------------|---------------------------|-----------------------|
| `print(x)`                | `say x`                   | `out x`               |
| `x = 5`                   | `set x to 5`              | `let x 5`             |
| `x += 1`                  | `change x by 1`           | `up x`                |
| `name = input("Name? ")`  | `ask "Name?" into name`   | `in name "Name?"`     |
| `if` / `elif` / `else`    | `if` / `else if` / `else` | `when` / `else when` / `else` |
| (indentation)             | `end if`                  | `.`                   |
| `for i in range(1, 11):`  | `for i from 1 to 10`      | `loop i 1..10`        |
| `for x in items:`         | `for each x in items`     | `loop x items`        |
| `while x < 5:`            | `repeat while x < 5`      | `loop while x < 5`    |
| `break` / `continue`      | `stop` / `skip`           | `stop` / `skip`       |
| `def f(a, b):`            | `define f(a, b)`          | `fn f a b`            |
| `return x`                | `return x`                | `ret x`               |
| `items.append(x)`         | `add x to items`          | `add items x`         |
| `items.remove(x)`         | `remove x from items`     | `del items x`         |
| `x in items`              | `x in items`              | `items has x`         |
| `len(x)`                  | `length(x)`               | `len(x)`              |
| `items[0]`                | `items[1]`                | `items[1]`            |
| `# comment`               | `# comment`               | `;; comment`          |
| `None`                    | `nothing`                 | `none`                |

If you type a word from another language by mistake, SimpleTalk tells you the right one.

## 13. Stability promise

From version 2.0, programs that work keep working:
- Keywords and built-in names won't be renamed or removed in any 2.x release.
- New features may be **added** in 2.x (new built-ins, for example).
- Anything that would break existing programs waits for version 3.0 and is listed in `CHANGELOG.md`.
