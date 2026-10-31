# Repeating things

Every repetition in SimpleTalk uses one word: `loop`. What follows it decides what kind of loop it is.

| Write | Does |
|---|---|
| `loop 3` | 3 times |
| `loop i 1..10` | counts from 1 to 10, putting each number in `i` |
| `loop x my_list` | goes through every item of a list |
| `loop while x < 10` | repeats while the check is true |
| `loop` | repeats forever, until `stop` |

## A number of times

```simp
loop 3
    out "Hip hip hooray!"
.
```

```output
Hip hip hooray!
Hip hip hooray!
Hip hip hooray!
```

The number can be worked out: `loop n * 2` is fine. It must be a whole number that isn't negative.

## Counting

`a..b` is a **range**: every whole number from a to b, including both ends. If the end is smaller than the start, it counts down.

```simp
loop i 1..5
    out "{i} x 7 = {i * 7}"
.
out "Countdown:"
loop i 3..1
    out i
.
out "Lift off!"
```

```output
1 x 7 = 7
2 x 7 = 14
3 x 7 = 21
4 x 7 = 28
5 x 7 = 35
Countdown:
3
2
1
Lift off!
```

A range on its own is a list, so you can print it or store it:

```simp
out 1..5
```

```output
[1, 2, 3, 4, 5]
```

Looping over a range doesn't build the list, so even `loop i 1..10000000` uses almost no memory.

## Going through a list

Give the loop a name, then a list. Each item is put into the name in turn.

```simp
loop fruit ["apple", "banana", "cherry"]
    out "I like", fruit
.
```

```output
I like apple
I like banana
I like cherry
```

Text works too, one letter at a time:

```simp
loop letter "abc"
    out upper(letter)
.
```

```output
A
B
C
```

How SimpleTalk tells `loop n` (repeat n times) from `loop i items` (go through items): if the loop's first word is a name followed by a value, it's the loop's name.

## While something is true

```simp
let n 1
loop while n < 100
    let n n * 2
.
out "First power of 2 above 100 is", n
```

```output
First power of 2 above 100 is 128
```

## Forever, with stop and skip

Inside any loop:

- `stop` leaves the loop straight away.
- `skip` jumps to the next round.

```simp
let i 0
loop
    up i
    when i = 3
        skip
    .
    when i > 5
        stop
    .
    out i
.
```

```output
1
2
4
5
```

A loop that never reaches `stop` runs until you stop the program: Ctrl+C in a terminal, or **Stop** in the playground.

## Loops inside loops

```simp
loop row 1..3
    let line ""
    loop col 1..3
        let line line + txt(row * col) + " "
    .
    out line
.
```

```output
1 2 3 
2 4 6 
3 6 9 
```
