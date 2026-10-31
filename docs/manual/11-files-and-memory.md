# Files and remembered values

## Text files

| Function | Does |
|---|---|
| `read("notes.txt")` | gives back all the text in the file |
| `write("notes.txt", text)` | saves text to the file, replacing what was there |
| `exists("notes.txt")` | `true` if the file is there |

File names are found **next to your program**, so a program finds its files wherever you run it from. Folders work too: `read("data/notes.txt")`.

```simp files
write("shopping.txt", "milk\neggs\nbread")
let items split(read("shopping.txt"), "\n")
out "The list has", len(items), "items:", join(items, ", ")
```

```output
The list has 3 items: milk, eggs, bread
```

To add to a file instead of replacing it, read it first:

```simp files
let log ""
when exists("log.txt")
    let log read("log.txt")
.
write("log.txt", log + "Program ran\n")
```

Reading a file that doesn't exist is a problem you can catch with `try` (chapter 10).

## JSON files: saving lists and maps

`save` writes any list, map, number, text, `true`/`false` or `none` to a JSON file, and `load` reads it back. JSON is a common format that most other programs understand too.

```simp files
let profile {name: "Bicky", langs: ["SimpleTalk", "Python"], level: 3}
save("profile.json", profile)

let again load("profile.json")
out again.name, "knows", join(again.langs, " and ")
```

```output
Bicky knows SimpleTalk and Python
```

The file `profile.json` looks like this, so you can also edit it by hand:

```json
{
  "name": "Bicky",
  "langs": [
    "SimpleTalk",
    "Python"
  ],
  "level": 3
}
```

Functions and tasks can't be saved; SimpleTalk tells you if you try.

## keep: values remembered between runs

`keep` makes a variable that **remembers its value the next time the program runs**. The value after the name is only used the very first time.

```simp norun
keep runs 0
up runs
out "You have run this program {runs} time(s)."
```

Run it three times:

```bash
$ simpletalk counter.simp
You have run this program 1 time(s).
$ simpletalk counter.simp
You have run this program 2 time(s).
$ simpletalk counter.simp
You have run this program 3 time(s).
```

How it works:

- Kept values are saved when the program ends, even if it stops with a problem, in a file next to it: `counter.simp` saves to `counter.memory.json`.
- Delete that file to start fresh.
- Lists and maps can be kept too, so a small to-do app needs no database:

```simp norun
keep todo []
in item "New task (or press Enter to just list them):"
when item != ""
    add todo item
.
loop t todo
    out "-", t
.
```

In the playground, `keep` remembers values in your browser.

On your computer, `keep` works only when you run a file with `simpletalk file.simp`. In interactive mode there's no file, so nothing is saved.
