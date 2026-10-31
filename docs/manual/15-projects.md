# Two small projects

These two programs bring the earlier chapters together. Each one is built in steps, and each step runs on its own, so you can follow along in the [playground](https://bicky21.github.io/SimpleTalk/).

## Project 1: a quiz

### Step 1: one question

```simp input=Kolkata
in answer "What is the capital of West Bengal?"
when lower(trim(answer)) = "kolkata"
    out "Correct!"
else
    out "Not quite, it's Kolkata."
.
```

```output
What is the capital of West Bengal? Kolkata
Correct!
```

`trim` removes spaces the player typed by accident, and `lower` makes "KOLKATA" and "kolkata" count the same.

### Step 2: many questions, kept in a list of maps

```simp input=Kolkata|8|blue
let questions [
    {ask: "What is the capital of West Bengal?", answer: "kolkata"},
    {ask: "What is 2 to the power of 3?", answer: "8"},
    {ask: "Which keyword closes a block in SimpleTalk? (word)", answer: "dot"}
]

let score 0
loop q questions
    in reply q.ask
    when lower(trim(txt(reply))) = q.answer
        out "Correct!"
        up score
    else
        out "The answer was:", q.answer
    .
.
out "You scored {score} out of {len(questions)}."
```

```output
What is the capital of West Bengal? Kolkata
Correct!
What is 2 to the power of 3? 8
Correct!
Which keyword closes a block in SimpleTalk? (word) blue
The answer was: dot
You scored 2 out of 3.
```

Why `txt(reply)`: `in` turns the answer "8" into the number 8, and `txt` turns it back into text so it can be compared with `"8"`.

### Step 3: a verdict with pick, and a best score that is remembered

```simp norun
keep best 0

;; ... the questions and the loop from step 2 go here ...

let percent round(score / len(questions) * 100)
pick percent
is 100
    out "Perfect!"
is 60..99
    out "Well done."
else
    out "Keep practising, you'll get there."
.

when score > best
    out "New best score!"
    let best score
.
```

Save the whole thing as `quiz.simp` and run it a few times. `keep` remembers your best score between runs.

## Project 2: a grade book

### Step 1: the data, and a function with tests

```simp
let students [
    {name: "Asha", marks: [88, 92, 79]},
    {name: "Ravi", marks: [55, 61, 48]},
    {name: "Meera", marks: [95, 99, 97]}
]

fn average numbers
    ret round(sum(numbers) / len(numbers), 1)
.

test average([90, 80]) = 85
test average([1, 2]) = 1.5
```

```output
[test] 2 tests passed.
```

Writing tests first means you find mistakes in `average` straight away, not after the report looks wrong.

### Step 2: a report

```simp
let students [
    {name: "Asha", marks: [88, 92, 79]},
    {name: "Ravi", marks: [55, 61, 48]},
    {name: "Meera", marks: [95, 99, 97]}
]

fn average numbers
    ret round(sum(numbers) / len(numbers), 1)
.

fn grade avg
    pick avg
    is 90..100
        ret "A"
    is 75..89.9
        ret "B"
    is 50..74.9
        ret "C"
    .
    ret "needs support"
.

loop s students
    let avg average(s.marks)
    out "{s.name}: {avg} ({grade(avg)})"
.

let averages students | each average(it.marks)
out "Class average:", average(averages)
out "Top students:", students | only average(it.marks) >= 85 | each it.name | join(", ")
```

```output
Asha: 86.3 (B)
Ravi: 54.7 (C)
Meera: 97 (A)
Class average: 79.3
Top students: Asha, Meera
```

### Step 3: save the report

Add this at the end to keep a copy of the results that other programs (or a spreadsheet) can read:

```simp norun
let report students | each {name: it.name, average: average(it.marks)}
save("report.json", report)
out "Saved report.json"
```

## Where next

- Load `report.json` back with `load` in another program and draw a bar chart in text: for each student, build a bar by adding `"#"` to a text in a `loop`, one `#` for every 10 marks.
- Turn the quiz into a two-player game with a map of scores.
- Put `average` and `grade` in `lib/grades.simp` and `use` them from both programs.
