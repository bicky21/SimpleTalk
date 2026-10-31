# Checking your work

SimpleTalk has tools for understanding and checking programs built in, so you don't need to install anything else.

## test

`test` checks that something is true. Put tests right next to the code they check.

```simp
fn square n
    ret n * n
.
test square(3) = 9
test square(-4) = 16
test [1, 2, 3] has 2
```

```output
[test] 3 tests passed.
```

Passing tests are quiet, and you get one summary line at the end. When a test fails, SimpleTalk stops and shows **both sides**, so you can see straight away what went wrong:

```simp error
fn square n
    ret n * 2          ;; a bug: this doubles instead of squaring
.
test square(3) = 9
```

```output
Oops! Something went wrong while running on line 4:

    4 | test square(3) = 9
        ^

  Test failed: square(3) = 9
  Hint: The left side is 6 and the right side is 9.
```

## watch

`watch name` reports every change to a variable from then on: the line that changed it, the new value, and the old one. It's an easy way to see what a loop is really doing.

```simp
let score 0
watch score
loop round 1..3
    up score round * 10
.
```

```output
[watch] line 2: watching score, now 0
[watch] line 4: score = 10  (was 0)
[watch] line 4: score = 30  (was 10)
[watch] line 4: score = 60  (was 30)
```

Watching a list or map also reports `add`, `del` and changes to its items. `watch a b` watches several names.

## Explain: your program in plain English

`simpletalk --explain file.simp` (or **Explain** in the playground and in VS Code) describes each line in words, without running anything. It's a good way to check that a program says what you meant.

```bash
$ simpletalk --explain examples/03_decisions.simp
What examples/03_decisions.simp does:

   2  Store 72 in marks.
   4  If marks is at least 90:
   5      Show "Grade A"
      Otherwise, if marks is at least 70:
   7      Show "Grade B"
      ...
```

## Trace: watch it run

`simpletalk --trace file.simp` (or **Trace** in VS Code) shows each line just before it runs, so you can follow the path the program really takes:

```bash
$ simpletalk --trace examples/02_variables.simp
  > line 2   | let name "Bicky"
  > line 3   | let age 20
  > line 4   | out "Hi {name}, you are {age} years old."
Hi Bicky, you are 20 years old.
```

## Check: find mistakes without running

`simpletalk --check file.simp` reads the program and reports mistakes in how it's written, without running it. VS Code does this every time you save, and underlines the mistake in red.
