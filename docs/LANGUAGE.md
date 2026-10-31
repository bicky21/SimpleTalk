# The SimpleTalk Language Guide (version 1.0)

SimpleTalk is designed around three rules:

1. **Read like English.** `set score to 10`, `repeat 3 times`, `add "milk" to shopping`.
2. **One way to do each thing.** Fewer things to remember.
3. **Never crash with a scary error.** Every mistake gets a line number, a `^` marker and a hint.

There are only **34 keywords** and **23 built-in functions**. This page lists all of them.

---

## 1. The basics

```
# Anything after a hash is a comment.
say "Hello!"                # show something
say "Total:", 5 + 5         # commas separate values (printed with a space)
```

- One instruction per line. Indentation is optional (but makes code easier to read).
- Keywords are not case-sensitive: `say`, `Say` and `SAY` all work.
- Names are case-sensitive: `score` and `Score` are different variables.

## 2. Values

| Kind      | Examples                    | Notes                                      |
|-----------|-----------------------------|--------------------------------------------|
| number    | `42`, `3.5`, `-7`, `1_000`  | `7 / 2` is `3.5`, `6 / 3` is `2`            |
| text      | `"hello"`, `'hi'`           | `{name}` inside text inserts a value       |
| boolean   | `true`, `false`             | the answer to a question like `x > 3`      |
| list      | `[1, 2, 3]`, `[]`           | positions start at **1**                   |
| nothing   | `nothing`                   | "no value"                                 |
| function  | `define ...`, `length`      | something you can call with `( )`          |

### Text tricks
```
set name to "Bicky"
say "Hi {name}, 2 + 2 is {2 + 2}"     # Hi Bicky, 2 + 2 is 4
say "Use {{ and }} for real braces"   # Use { and } for real braces
say "Line one\nLine two"              # \n = new line, \t = tab, \" = quote
say "Age: " + 12                      # text + anything = joined text
```

## 3. Variables

```
set age to 20          # create or replace
change age by 1        # add to a number (use a negative number to subtract)
ask "Your name?" into name   # ask the user; typed numbers become real numbers
```

## 4. Maths and comparisons

| Write            | Meaning                         |
|------------------|---------------------------------|
| `+ - * /`        | add, subtract, multiply, divide |
| `mod`            | remainder: `10 mod 3` is `1`    |
| `=` or `is`      | equal                           |
| `!=` or `is not` | not equal                       |
| `< > <= >=`      | less / greater                  |
| `in`             | `"a" in my_list`, `"ell" in "hello"` |
| `and or not`     | combine true/false answers      |

Order: brackets, then `- (negative)`, then `* / mod`, then `+ -`, then comparisons, then `not`, `and`, `or`.

Only compare two things at once: write `x > 1 and x < 10`, not `1 < x < 10`.

## 5. Decisions

```
if marks >= 90 then
    say "A"
else if marks >= 70 then
    say "B"
else
    say "Keep going!"
end if
```

- `then` is optional.
- The condition must be `true` or `false` (SimpleTalk won't guess what `if 5` means).
- Close every block with `end`. You may write `end if`, `end repeat`, `end for` or `end define` to be extra clear — if you do, SimpleTalk checks that it matches.

## 6. Loops

```
repeat 3 times              # a fixed number of times
    say "hi"
end repeat

repeat while x < 10         # while something is true
    change x by 1
end repeat

repeat until x = 0          # until something becomes true
    change x by -1
end repeat

repeat forever              # until you 'stop'
    ...
end repeat

for i from 1 to 10          # counting (both ends included)
    say i
end for

for i from 10 to 1          # counts down automatically
    say i
end for

for each fruit in fruits    # every item of a list (or letter of a text)
    say fruit
end for
```

Inside any loop:
- `stop` leaves the loop now.
- `skip` jumps to the next round.

## 7. Lists

```
set shopping to ["milk", "eggs"]
add "bread" to shopping           # put at the end
remove "eggs" from shopping       # remove the first match
set shopping[1] to "oat milk"     # change an item
say shopping[1]                   # first item
say shopping[-1]                  # last item
say length(shopping)              # how many items
if "bread" in shopping then ...
```

Positions start at **1** (like counting in real life). `[0]` is an error with a helpful hint.
Text works the same way: `"hello"[1]` is `"h"`.

## 8. Functions

```
define greet(name)
    say "Hello, {name}!"
end define

define area(width, height)
    return width * height
end define

greet("Bicky")
say area(3, 4)
```

- A function without `return` gives back `nothing`.
- Parameters (like `name`) belong to the function.
- `set` inside a function changes an outer variable **if it already exists**; otherwise it makes a new variable that only lives inside the function.
- Functions can call themselves (recursion) up to 1000 levels deep.

## 9. Built-in functions

| Function                | Example                                 |
|-------------------------|-----------------------------------------|
| `length(x)`             | `length("hello")` → `5`                 |
| `number(x)`             | `number("42")` → `42`                   |
| `is_number(x)`          | `is_number("4.5")` → `true`             |
| `text(x)`               | `text(42)` → `"42"`                     |
| `type(x)`               | `type([1])` → `"list"`                  |
| `round(x, digits)`      | `round(3.14159, 2)` → `3.14` (2.5 → 3)  |
| `abs(x)`                | `abs(-5)` → `5`                         |
| `sqrt(x)`               | `sqrt(16)` → `4`                        |
| `power(x, y)`           | `power(2, 10)` → `1024`                 |
| `random(low, high)`     | `random(1, 6)` → a whole number 1 to 6  |
| `min(...)` / `max(...)` | `max(3, 9, 2)` or `max(my_list)`        |
| `sum(list)`             | `sum([1, 2, 3])` → `6`                  |
| `upper(t)` / `lower(t)` | `upper("hi")` → `"HI"`                  |
| `trim(t)`               | `trim("  hi ")` → `"hi"`                |
| `replace(t, old, new)`  | `replace("cat", "c", "b")` → `"bat"`    |
| `split(t, sep)`         | `split("a,b", ",")` → `["a", "b"]`      |
| `join(list, sep)`       | `join(["a", "b"], "-")` → `"a-b"`       |
| `sort(list)`            | `sort([3, 1, 2])` → `[1, 2, 3]` (new list) |
| `reverse(x)`            | `reverse("abc")` → `"cba"` (new value)  |
| `copy(list)`            | a separate copy of a list               |
| `wait(seconds)`         | `wait(0.5)` pauses half a second        |

## 10. All keywords

```
say ask into
set to change by add remove from
if then else end
repeat times while until forever for each in stop skip
define return
and or not is mod true false nothing
```

These can't be used as variable names.

## 11. Coming from Python?

| Python                    | SimpleTalk                        |
|---------------------------|-----------------------------------|
| `print(x)`                | `say x`                           |
| `x = 5`                   | `set x to 5`                      |
| `x += 1`                  | `change x by 1`                   |
| `name = input("Name? ")`  | `ask "Name?" into name`           |
| `elif`                    | `else if`                         |
| `for i in range(1, 11):`  | `for i from 1 to 10`              |
| `while x < 5:`            | `repeat while x < 5`              |
| `break` / `continue`      | `stop` / `skip`                   |
| `def f(a):`               | `define f(a)`                     |
| `lst.append(x)`           | `add x to lst`                    |
| `len(x)`                  | `length(x)`                       |
| `lst[0]`                  | `lst[1]`                          |
| `x % 2`                   | `x mod 2`                         |
| `True / False / None`     | `true / false / nothing`          |

If you type the Python word by mistake, SimpleTalk tells you the right one.

## 12. Stability promise

From version 1.0, programs that work keep working:
- Keywords and built-in names won't be renamed or removed in any 1.x release.
- New features may be **added** in 1.x (new built-ins, for example).
- Anything that would break existing programs waits for version 2.0 and is listed in `CHANGELOG.md`.
