# Coming from Python

If you already know Python, this table translates the common things. If you type the Python word by mistake, SimpleTalk tells you the right one.

| Python | SimpleTalk |
|---|---|
| `print(x, y)` | `out x, y` |
| `# comment` | `;; comment` |
| `x = 5` | `let x 5` |
| `x += 1` / `x -= 2` | `up x` / `up x -2` |
| `name = input("Name? ")` | `in name "Name?"` |
| `f"Hi {name}"` | `"Hi {name}"` |
| `if` / `elif` / `else:` | `when` / `else when` / `else` |
| indentation ends a block | a line with `.` ends a block |
| `x == y`, `x != y` | `x = y`, `x != y` |
| `x in items` | `items has x` |
| `x % 2` | `x mod 2` |
| `True`, `False`, `None` | `true`, `false`, `none` |
| `for _ in range(3):` | `loop 3` |
| `for i in range(1, 11):` | `loop i 1..10` |
| `for x in items:` | `loop x items` |
| `while x < 5:` | `loop while x < 5` |
| `while True:` | `loop` |
| `break` / `continue` | `stop` / `skip` |
| `def area(w, h):` | `fn area w h` |
| `return x` | `ret x` |
| `lambda n: n * 2` | `fn n -> n * 2` |
| `items[0]`, `items[-1]` | `items[1]`, `items[-1]` |
| `items.append(x)` | `add items x` |
| `items.remove(x)` | `del items x` |
| `len(x)` | `len(x)` |
| `str(x)`, `int(x)`, `float(x)` | `txt(x)`, `num(x)`, `num(x)` |
| `d = {"a": 1}`; `d["a"]` | `let d {a: 1}`; `d.a` or `d["a"]` |
| `del d["a"]` | `del d "a"` |
| `[x * 2 for x in xs if x > 1]` | `xs \| only it > 1 \| each it * 2` |
| `match x:` / `case 1:` | `pick x` / `is 1` |
| `try:` / `except Exception as e:` | `try` / `fail e` |
| `raise ValueError("bad")` | `oops "bad"` |
| `import shapes` | `use "shapes"` |
| `open(f).read()` | `read(f)` |
| `json.load(open(f))` | `load(f)` |
| `assert square(3) == 9` | `test square(3) = 9` |
| `asyncio.create_task(...)` / `await t` | `task t` … `.` / `await t` |

## Things that work differently

- **Positions start at 1.** `items[1]` is the first item. `items[0]` is a friendly error.
- **Checks must be true or false.** `when items` isn't allowed; write `when len(items) > 0`.
- **Division always gives the real answer.** `7 / 2` is `3.5`, and `6 / 3` is `2`.
- **Adding text to anything joins them.** `"Age: " + 12` is `"Age: 12"`; Python would complain.
- **`let` inside a function changes an outer variable if it already exists.** Python would need `global`.
- **A function is called with no space before the bracket.** `area(3, 4)` works, `area (3, 4)` doesn't.

```simp
let items [10, 20, 30]
out items[1], items[-1], 7 / 2, 6 / 3, "Age: " + 12
```

```output
10 30 3.5 2 Age: 12
```
