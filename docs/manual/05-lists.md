# Lists

A list keeps several values in order. Write it with square brackets and commas.

```simp
let shopping ["milk", "eggs", "bread"]
out shopping
out len(shopping), "items"
```

```output
["milk", "eggs", "bread"]
3 items
```

Lists can hold any mix of values, including other lists.

## Positions start at 1

The first item is at position 1, like counting in real life. Negative positions count from the end, so `-1` is the last item.

```simp
let days ["mon", "tue", "wed", "thu", "fri"]
out days[1], days[2], days[-1]
```

```output
mon tue fri
```

There must be **no space** before the `[`. `days[1]` picks an item, while `days [1]` would be the name `days` followed by a separate list.

Position 0 doesn't exist, and SimpleTalk says so:

```simp error
let days ["mon", "tue"]
out days[0]
```

```output
Oops! Something went wrong while running on line 2:

    2 | out days[0]
                ^

  Positions start at 1 in SimpleTalk, so [0] doesn't exist.
  Hint: Use [1] for the first item and [-1] for the last.
```

## Changing a list

| Write | Does |
|---|---|
| `add items x` | puts x at the end |
| `del items x` | removes the first x |
| `let items[2] x` | replaces the item at position 2 |

```simp
let shopping ["milk", "eggs"]
add shopping "bread"
del shopping "eggs"
let shopping[1] "oat milk"
out shopping
```

```output
["oat milk", "bread"]
```

`del` on an item that isn't there is a mistake. Check first with `has`:

```simp
let shopping ["milk"]
when shopping has "eggs"
    del shopping "eggs"
else
    out "No eggs to remove"
.
```

```output
No eggs to remove
```

## Useful functions for lists

```simp
let scores [70, 95, 40, 82]
out len(scores), sum(scores), min(scores), max(scores)
out sort(scores)
out rev(scores)
out join(["a", "b", "c"], "-")
out split("red,green,blue", ",")
```

```output
4 287 40 95
[40, 70, 82, 95]
[82, 40, 95, 70]
a-b-c
["red", "green", "blue"]
```

`sort` and `rev` give back a **new** list and leave the original as it was. Joining two lists with `+` also makes a new list: `[1, 2] + [3]` is `[1, 2, 3]`.

## Lists are shared, not copied

When you `let` one name to another list, both names point at the **same** list. Changing it through one name changes what the other sees. Use `copy(...)` when you want a separate list.

```simp
let a [1, 2]
let b a
let c copy(a)
add a 3
out a, b, c
```

```output
[1, 2, 3] [1, 2, 3] [1, 2]
```

## Going through a list

```simp
let total 0
loop n [5, 10, 15]
    up total n
.
out "Total:", total
```

```output
Total: 30
```

The loop goes through a copy of the list, so it's safe to `add` or `del` items inside the loop.

For filtering and transforming lists in one line, see [Pipelines](08-pipelines.md).
