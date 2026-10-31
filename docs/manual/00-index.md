# The SimpleTalk Manual

SimpleTalk is a small programming language for people writing their first programs. It uses short words, closes every block with a single dot, and when something goes wrong it tells you where, why, and how to fix it.

```simp
let name "Bicky"
out "Hello, {name}!"

loop i 1..3
    out "SimpleTalk is easy, line {i}"
.
```

```output
Hello, Bicky!
SimpleTalk is easy, line 1
SimpleTalk is easy, line 2
SimpleTalk is easy, line 3
```

Every example in this manual has a **Try it** button that opens it in the [playground](https://bicky21.github.io/SimpleTalk/), where you can run and change it. Nothing needs to be installed.

## How this manual is organised

**Learning the language.** Read these in order the first time.

1. [Getting started](01-getting-started.md): run your first program in the browser, the terminal, or VS Code.
2. [First steps](02-first-steps.md): showing things, storing values, asking questions.
3. [Making decisions](03-decisions.md): `when`, `else`, and comparing values.
4. [Repeating things](04-loops.md): every kind of `loop`.
5. [Lists](05-lists.md): keeping many values in order.
6. [Maps](06-maps.md): keeping values under names.
7. [Functions](07-functions.md): making your own commands with `fn`.

**Going further.** Read any of these when you need them.

8. [Pipelines](08-pipelines.md): transforming lists in one readable line.
9. [Choosing with pick](09-pick.md): matching a value against several choices.
10. [When things go wrong](10-problems.md): reading error messages, `try`, `fail` and `oops`.
11. [Files and remembered values](11-files-and-memory.md): reading, writing, JSON and `keep`.
12. [Using other files](12-modules.md): splitting a program up with `use`.
13. [Tasks](13-tasks.md): doing things side by side.
14. [Checking your work](14-checking.md): `test`, `watch`, Explain and Trace.

**Putting it together.**

15. [Two small projects](15-projects.md): a quiz and a grade book, built step by step.
16. [Reference](16-reference.md): every keyword, operator and built-in function on one page.
17. [Coming from Python](17-from-python.md): a side-by-side translation table.

## About

SimpleTalk is developed by **Bicky Prasad Yadav** and **Claude**. The language, its playground, the VS Code extension and this manual are all open source on [GitHub](https://github.com/bicky21/SimpleTalk).
