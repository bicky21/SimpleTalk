# Choosing with pick

`pick` compares one value with several choices and runs the first one that matches. It's a tidy alternative to a long `when` / `else when` chain.

```simp
let day "sun"
pick day
is "sat", "sun"
    out "Weekend!"
is "mon", "tue", "wed", "thu", "fri"
    out "Work day"
else
    out "That isn't a day"
.
```

```output
Weekend!
```

- Each choice starts with `is`, followed by one or more values separated by commas.
- `else` catches everything that didn't match. It's optional, and must come last.
- One dot closes the whole `pick`.

## Ranges as choices

A range like `90..100` matches any number between the two ends, including decimals:

```simp
loop marks [95, 82.5, 61, 30]
    pick marks
    is 90..100
        out marks, "A"
    is 75..89.99
        out marks, "B"
    is 50..74.99
        out marks, "C"
    else
        out marks, "Needs help"
    .
.
```

```output
95 A
82.5 B
61 C
30 Needs help
```

## pick compared with when

These two do the same thing:

```simp
let n 3
pick n
is 1
    out "one"
is 2, 3
    out "two or three"
.

when n = 1
    out "one"
else when n = 2 or n = 3
    out "two or three"
.
```

```output
two or three
two or three
```

Use `pick` when you're comparing **one value** with fixed choices. Use `when` when each check is different, like `when age > 18 and has_ticket`.

`is` only has a meaning inside `pick`. To compare two values anywhere else, use `=`.
