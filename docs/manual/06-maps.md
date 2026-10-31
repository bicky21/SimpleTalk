# Maps

A map keeps values under names, called **keys**, like the fields of a contact card. Write it with curly braces, `key: value` pairs and commas.

```simp
let me {name: "Bicky", age: 20, city: "Kolkata"}
out me
out me.name, "is", me.age
```

```output
{name: "Bicky", age: 20, city: "Kolkata"}
Bicky is 20
```

## Reading and changing values

| Write | Does |
|---|---|
| `me.name` | the value under the key `name` |
| `me["name"]` | the same, when the key is in a variable or has spaces |
| `let me.age 21` | changes a value, or adds a new key |
| `del me "age"` | removes a key |
| `me has "age"` | `true` if the key is there |

```simp
let me {name: "Bicky", "fav food": "momo"}
let me.age 21
let key "fav food"
out me[key]
del me "fav food"
out me, me has "age", me has "fav food"
```

```output
momo
{name: "Bicky", age: 21} true false
```

The dot must touch both sides: `me.name` reads a value, while a `.` alone on a line closes a block.

Reading a key that isn't there is a mistake, and SimpleTalk suggests the key you probably meant:

```simp error
let me {name: "Bicky"}
out me.nmae
```

```output
Oops! Something went wrong while running on line 2:

    2 | out me.nmae
              ^

  This map has no 'nmae'.
  Hint: Did you mean 'name'?
```

## Going through a map

Looping over a map gives its keys, in the order they were added. `keys(...)` and `values(...)` give them as lists.

```simp
let stock {apples: 12, pears: 0, plums: 5}
loop fruit stock
    when stock[fruit] = 0
        out fruit, "are sold out"
    else
        out fruit, stock[fruit]
    .
.
out keys(stock), sum(values(stock)), len(stock)
```

```output
apples 12
pears are sold out
plums 5
["apples", "pears", "plums"] 17 3
```

## Maps and lists together

Maps and lists can hold each other, which is how you describe real things:

```simp
let student {name: "Asha", subjects: ["DSA", "OS"], marks: {DSA: 88, OS: 79}}
add student.subjects "DBMS"
let student.marks.DBMS 91
out student.subjects
out student.marks
```

```output
["DSA", "OS", "DBMS"]
{DSA: 88, OS: 79, DBMS: 91}
```

A list of maps works like a small table:

```simp
let people [{name: "Asha", age: 20}, {name: "Ravi", age: 17}]
loop p people
    out "{p.name} is {p.age}"
.
```

```output
Asha is 20
Ravi is 17
```

Like lists, maps are shared: `let b a` gives a second name for the same map.
