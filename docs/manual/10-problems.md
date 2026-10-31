# When things go wrong

## Reading an error message

Every problem SimpleTalk reports has the same parts:

```simp error
let name "Bicky"
out "Hi {nmae}"
```

```output
Oops! Something went wrong while running on line 2:

    2 | out "Hi {nmae}"
                 ^

  I don't know what 'nmae' is.
  Hint: Did you mean 'name'?
```

1. **Where**: the line number, the line itself, and a `^` under the exact spot.
2. **What** went wrong, in plain words.
3. A **hint** for fixing it, when SimpleTalk can guess one.

There are two kinds of problem:

- *"I could not understand the code"* means the program is written in a way SimpleTalk can't read. It's found **before** anything runs, and `simpletalk --check` finds it too.
- *"Something went wrong while running"* means the program was fine to read but hit a problem while running, like dividing by zero.

If you type a word from another language, SimpleTalk tells you the SimpleTalk word:

```simp error
print "hello"
```

```output
Oops! I could not understand the code on line 1:

    1 | print "hello"
        ^

  SimpleTalk doesn't use 'print'. The word for that is 'out'.
  Hint: Write 'out' instead of 'print'. All words are listed in docs/LANGUAGE.md.
```

## Catching problems with try and fail

`try` runs a block. If a problem happens inside it, SimpleTalk jumps to the `fail` part instead of stopping. The name after `fail` receives the problem's message.

```simp
try
    let age num("twenty")
    out "This line never runs"
fail why
    out "That didn't work:", why
.
out "The program carries on"
```

```output
That didn't work: "twenty" doesn't look like a number.
The program carries on
```

You can leave out the name if you don't need the message: write `fail` on its own.

`try` catches problems that happen **while running**. Mistakes in how the code is written are still reported before the program starts.

## Raising your own problem with oops

`oops "message"` stops the program with your own message. It's how a function says "I can't do that":

```simp
fn withdraw balance amount
    when amount > balance
        oops "Not enough money: you have {balance}, you asked for {amount}"
    .
    ret balance - amount
.

let balance 500
try
    let balance withdraw(balance, 200)
    let balance withdraw(balance, 900)
fail why
    out why
.
out "Balance is", balance
```

```output
Not enough money: you have 300, you asked for 900
Balance is 300
```

If nothing catches it, `oops` stops the program and shows your message where it happened:

```simp error
oops "Out of stock"
```

```output
Oops! The program stopped on line 1:

    1 | oops "Out of stock"
        ^

  Out of stock
```

## Problems that stop programs from freezing

Some mistakes would make a program run forever or crash. SimpleTalk stops these with a clear message instead:

- a function calling itself more than 1000 levels deep,
- a range too big to turn into a list (over 10 million items),
- `in age num` when there are no more answers to read.

And Ctrl+C (or **Stop** in the playground) always stops a running program cleanly.
