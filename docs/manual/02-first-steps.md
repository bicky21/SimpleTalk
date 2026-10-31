# First steps

## Showing things with out

`out` shows a value. Separate several values with commas, and they are printed with a space between them.

```simp
out "Hello"
out 7 * 6
out "The answer is", 42
out
out "(an empty out prints an empty line)"
```

```output
Hello
42
The answer is 42

(an empty out prints an empty line)
```

## Values

SimpleTalk has a few kinds of value:

| Kind | Examples | Notes |
|---|---|---|
| number | `42`, `3.5`, `-7`, `1_000_000` | `7 / 2` is `3.5`, and `6 / 3` is `2` |
| text | `"hello"`, `'hi'` | either kind of quote |
| bool | `true`, `false` | the answer to a question such as `x > 3` |
| list | `[1, 2, 3]` | chapter 5 |
| map | `{name: "Bicky"}` | chapter 6 |
| none | `none` | means "no value" |

`type(...)` tells you what kind a value is:

```simp
out type(42), type("hi"), type(true), type([1]), type(none)
```

```output
number text bool list none
```

## Storing values with let

`let` stores a value under a name. Use the name later to get the value back.

```simp
let name "Bicky"
let age 20
out name, "is", age
```

```output
Bicky is 20
```

`let` also replaces a value. You can use the old value to work out the new one:

```simp
let score 10
let score score * 2
out score
```

```output
20
```

Names can contain letters, digits and `_`, but can't start with a digit. They are case-sensitive: `score` and `Score` are different names. SimpleTalk's own words, like `let` or `loop`, can't be used as names.

## Adding to a number with up

`up` adds to a number. On its own it adds 1. Give it a negative number to subtract.

```simp
let lives 3
up lives
out lives
up lives 10
out lives
up lives -5
out lives
```

```output
4
14
9
```

## Text

Put `{...}` inside text to insert a value. Anything can go inside the braces, even sums.

```simp
let name "Asha"
let apples 4
out "{name} has {apples} apples, so {apples * 2} halves."
```

```output
Asha has 4 apples, so 8 halves.
```

A few special characters:

```simp
out "Line one\nLine two"
out "A tab:\tthere"
out "She said \"hi\""
out "Real braces: {{like this}}"
```

```output
Line one
Line two
A tab:	there
She said "hi"
Real braces: {like this}
```

Adding text to anything joins them into one text:

```simp
out "Age: " + 12
```

```output
Age: 12
```

## Maths

| Write | Means |
|---|---|
| `+ - * /` | add, subtract, multiply, divide |
| `mod` | remainder after dividing: `10 mod 3` is `1` |
| `( )` | do this part first |

```simp
out 2 + 3 * 4
out (2 + 3) * 4
out 10 / 4, 10 mod 4
out 0.1 + 0.2
```

```output
14
20
2.5 2
0.3
```

Results are tidied for you: `0.1 + 0.2` shows `0.3`, and `6 / 3` shows `2`, not `2.0`.

## Asking questions with in

`in` asks the person running the program a question and stores the answer:

```simp input=Bicky
in name "What is your name?"
out "Nice to meet you, {name}!"
```

```output
What is your name? Bicky
Nice to meet you, Bicky!
```

If the answer looks like a number, it becomes a real number, so you can do maths with it.

Often you need a particular kind of answer. Put `num` or `yes` after the name, and SimpleTalk keeps asking until the answer fits:

```simp input=twenty|20|maybe|yes
in age num "How old are you?"
in ready yes "Ready to start?"
out "In 5 years you will be", age + 5
out "ready is", ready
```

```output
How old are you? twenty
Please type a number.
How old are you? 20
Ready to start? maybe
Please answer yes or no.
Ready to start? yes
In 5 years you will be 25
ready is true
```

`yes` accepts *y, yes, ok, sure, haan* and *n, no, nope, nahi*, in any capitals, and stores `true` or `false`.

In the playground, type the answers in the **Answers for `in`** box, one per line, before pressing Run.
