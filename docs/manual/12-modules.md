# Using other files

As a program grows, split it into several files. `use` runs another `.simp` file once and brings in everything it defines: its functions and its variables.

**lib/geometry.simp**

```simp
let pi 3.14159

fn circle_area r
    ret round(pi * r * r, 2)
.

fn rect_area w h
    ret w * h
.
```

**main.simp**

```simp files
use "lib/geometry"

out "Circle:", circle_area(2)
out "Rectangle:", rect_area(3, 4)
out "pi is about", pi
```

```output
Circle: 12.57
Rectangle: 12
pi is about 3.14159
```

## The rules

- The path is relative to the folder of the file that says `use`, and `.simp` can be left out.
- Each file runs only once, however many times it is used.
- Names starting with `_` stay private to their file. Use them for helpers other files shouldn't see:

```simp
fn _round_money x
    ret round(x, 2)
.
fn with_tax price
    ret _round_money(price * 1.18)
.
```

- Two files can't `use` each other. SimpleTalk spots this and suggests moving the shared code into a third file.
- If a problem happens inside a used file, the message names that file and line:

```
Oops! Something went wrong while running on line 2 of lib/bad.simp:

    2 |     ret 1 / 0
                  ^

  You can't divide by zero.
```

In the playground, the examples' library files (like `lib/geometry`) are available to `use`.
