# Functions

A function is your own command: a block of code with a name, which you can run whenever you need it.

## Making and using a function

Write `fn`, the function's name, and the names of its inputs separated by spaces. The block ends with a `.` line. Call it with the name and the values in brackets, with **no space** before the `(`.

```simp
fn greet name
    out "Welcome, {name}!"
.

greet("Bicky")
greet("Asha")
```

```output
Welcome, Bicky!
Welcome, Asha!
```

## Giving back a value with ret

`ret` ends the function and gives a value back to wherever it was called:

```simp
fn area width height
    ret width * height
.

out area(3, 4)
let big area(10, 20)
out "Big room:", big
```

```output
12
Big room: 200
```

A function without `ret`, or with `ret` on its own, gives back `none`.

```simp
fn hello
    out "hi"
.
let result hello()
out result
```

```output
hi
none
```

A function with no inputs is still called with empty brackets: `hello()`.

## Decisions inside functions

`ret` can appear anywhere, and the function stops there:

```simp
fn grade marks
    when marks >= 90
        ret "A"
    .
    when marks >= 70
        ret "B"
    .
    ret "C"
.
out grade(95), grade(75), grade(40)
```

```output
A B C
```

## Functions that call themselves

A function may call itself, as long as it has a way to stop. This is called recursion.

```simp
fn factorial n
    when n <= 1
        ret 1
    .
    ret n * factorial(n - 1)
.
out factorial(10)
```

```output
3628800
```

If a function never stops calling itself, SimpleTalk stops it after 1000 levels and explains why:

```simp error
fn forever
    ret forever()
.
out forever()
```

```output
Oops! Something went wrong while running on line 2:

    2 |     ret forever()
                       ^

  Too many functions calling each other (more than 1000 deep).
  Hint: Does 'forever' keep calling itself forever? Make sure it can 'ret' without calling itself.
```

## Which variables a function can see

- A function's **inputs** belong to the function.
- Inside a function, `let` and `up` change an outer variable **if it already exists**. Otherwise `let` makes a new variable that exists only while the function runs.

```simp
let score 0
fn win points
    up score points
    let bonus 5
.
win(10)
win(3)
out score
```

```output
13
```

Here `score` already existed, so `win` changed it. `bonus` was new, so it disappeared when `win` finished.

## Quick functions

For small one-line functions, write `fn inputs -> value`. A quick function is a value: store it in a variable, or pass it to another function.

```simp
let double fn n -> n * 2
let plus fn a b -> a + b
out double(21), plus(2, 3)

fn apply f x
    ret f(x)
.
out apply(fn n -> n * n, 7)
```

```output
42 5
49
```

Functions remember the variables around them when they were made:

```simp
fn make_counter
    let count 0
    fn next
        up count
        ret count
    .
    ret next
.
let counter make_counter()
counter()
counter()
out counter()
```

```output
3
```
