# Tasks: doing things side by side

A task is a block of code that starts running straight away **alongside** the rest of your program. It's useful when something takes a while, like waiting for a download, and you want to get on with other work meanwhile.

```simp
task kettle
    wait(0.3)
    out "Kettle: water boiled"
    ret "hot water"
.

out "Me: setting the table while I wait..."
let water await kettle
out "Me: making tea with", water
```

```output
Me: setting the table while I wait...
Kettle: water boiled
Me: making tea with hot water
```

- `task name` starts the block straight away and moves on. The block ends with `.`.
- `await name` waits until the task has finished. Write `let x await name` to also get the value the task gave back with `ret`.
- `wait(seconds)` pauses, for example `wait(0.5)` for half a second.

## Several tasks at once

```simp
task fast
    wait(0.1)
    ret "fast is done"
.
task slow
    wait(0.3)
    ret "slow is done"
.
out await slow
out await fast
```

```output
slow is done
fast is done
```

Both tasks ran at the same time, so the whole program took about 0.3 seconds, not 0.4.

## Things to know

- Tasks **share variables** with the program. If two tasks change the same variable at the same moment, the result can be surprising, so it's best to have each task `ret` its result and combine the results after `await`.
- Tasks you never `await` still finish before the program ends.
- If a task hits a problem, it shows up at `await`, where `try` can catch it, or when the program ends:

```simp
task risky
    oops "the download failed"
.
try
    await risky
fail why
    out "Caught:", why
.
```

```output
Caught: the download failed
```

- Ctrl+C stops the program and all its tasks.
- **In the playground**, browsers don't allow this kind of task, so each task runs completely as soon as it starts. Programs still give the same results, but text may be printed in a different order.
