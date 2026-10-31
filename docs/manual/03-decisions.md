# Making decisions

## when

`when` runs a block only if a check is true. The block ends with a `.` line.

```simp
let temperature 32
when temperature > 30
    out "It's hot. Drink some water."
.
```

```output
It's hot. Drink some water.
```

## else and else when

Add `else` for what happens otherwise, and `else when` for more checks in between. SimpleTalk runs the **first** part whose check is true, and skips the rest. One dot closes the whole chain.

```simp
let marks 72

when marks >= 90
    out "Grade A"
else when marks >= 70
    out "Grade B"
else when marks >= 50
    out "Grade C"
else
    out "Keep practising"
.
```

```output
Grade B
```

## Comparing values

| Write | True when |
|---|---|
| `a = b` | a and b are equal |
| `a != b` | a and b are different |
| `a < b`, `a > b` | less than, greater than |
| `a <= b`, `a >= b` | less than or equal, greater than or equal |
| `list has x` | the list contains x, or the text contains x |

```simp
out 3 = 3, 3 != 4, 2 < 1, "a" = "a"
out [1, 2, 3] has 2, "hello" has "ell"
```

```output
true true false true
true true
```

Equality is careful: `1 = 1.0` is true, but the number `1` is not equal to the text `"1"`, and neither is equal to `true`.

```simp
out 1 = 1.0, 1 = "1", 1 = true
```

```output
true false false
```

Text compares in dictionary order, so `"apple" < "banana"` is true. You can't compare a number with text using `<`; turn the text into a number first with `num(...)`.

## and, or, not

```simp
let age 20
let has_ticket true

when age >= 18 and has_ticket
    out "Welcome to the show"
.
when not has_ticket or age < 18
    out "Sorry, you can't come in"
.
```

```output
Welcome to the show
```

`and` stops early if the left side is false, and `or` stops early if the left side is true, so the right side isn't even worked out.

Compare two things at a time. To check that a number is between two others, join two comparisons with `and`:

```simp
let x 5
out x > 1 and x < 10
```

```output
true
```

## Checks must be true or false

SimpleTalk doesn't guess what a check means. `when 5` is a mistake, because 5 is neither true nor false. Compare it with something instead:

```simp error
let count 5
when count
    out "something"
.
```

```output
Oops! Something went wrong while running on line 2:

    2 | when count
             ^

  'when' needs true or false, but got number 5.
  Hint: Compare it with something, like: x > 0  or  name != ""
```

For "is this list empty?" write `len(items) > 0`, and for "is this text empty?" write `name != ""`.
