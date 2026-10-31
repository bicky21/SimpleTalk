# Pipelines

A pipeline passes a value through steps, from left to right, using `|`. It's the shortest way to filter and transform a list.

```simp
let scores [70, 95, 40, 82, 55]
out scores | only it >= 60 | sort
```

```output
[70, 82, 95]
```

Read it aloud: *take scores, keep only the ones at least 60, then sort them.*

## The three kinds of step

| Step | Does |
|---|---|
| `\| only CHECK` | keeps the items where CHECK is true |
| `\| each VALUE` | turns every item into VALUE |
| `\| name` or `\| name(more)` | calls a function with the whole value first: `\| join(", ")` means `join(value, ", ")` |

Inside `only` and `each`, the word `it` means the current item.

```simp
let scores [70, 95, 40, 82, 55]
out scores | each it + 5
out scores | only it < 60 | len
out scores | each it * 2 | only it > 150 | sum
```

```output
[75, 100, 45, 87, 60]
2
354
```

Steps that call a function work on anything, not just lists:

```simp
out "red,green,blue" | split(",") | each upper(it) | join(" + ")
```

```output
RED + GREEN + BLUE
```

## With your own functions

Any function can be a step, and quick functions fit nicely in `each`:

```simp
fn initial name
    ret upper(name[1])
.
let names ["asha", "ravi", "meera"]
out names | each initial(it) | join("")

let bonus fn s -> round(s * 1.1)
out [70, 95, 40] | each bonus(it)
```

```output
ARM
[77, 105, 44]
```

## With maps

A list of maps filters nicely:

```simp
let people [{name: "Asha", age: 20}, {name: "Ravi", age: 17}, {name: "Meera", age: 25}]
out people | only it.age >= 18 | each it.name | join(", ")
```

```output
Asha, Meera
```

## Compared with a loop

This pipeline:

```simp
out [1, 2, 3, 4, 5, 6] | only it mod 2 = 0 | each it * it
```

```output
[4, 16, 36]
```

does the same as this loop:

```simp
let result []
loop n [1, 2, 3, 4, 5, 6]
    when n mod 2 = 0
        add result n * n
    .
.
out result
```

```output
[4, 16, 36]
```

Use whichever reads more clearly to you. Pipelines are good for short chains, and loops are better when each step needs several lines.
