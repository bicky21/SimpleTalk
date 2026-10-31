# Getting started

There are three ways to run SimpleTalk. Pick whichever suits you; the language is the same everywhere.

## In your browser (nothing to install)

Open the [SimpleTalk playground](https://bicky21.github.io/SimpleTalk/). The first visit downloads the engine (about 10 MB, only once). When the bottom of the page says *Ready*, type a program on the left and press **Run** or Ctrl+Enter.

- **Examples** loads any of the sample programs.
- **Explain** describes your program in plain English.
- **Share** copies a link to your program, so someone else can open exactly what you wrote.
- If your program asks questions with `in`, type the answers in the **Answers for `in`** box, one per line.

In the browser, tasks (chapter 13) run one after another instead of side by side. Everything else works the same as on your computer.

## On your computer

You need Python 3.10 or newer.

```bash
git clone https://github.com/bicky21/SimpleTalk.git
cd SimpleTalk
python3 -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -e .
```

Now write a program in a file ending in `.simp`, for example `hello.simp`:

```simp
out "Hello, World!"
```

```output
Hello, World!
```

and run it:

```bash
simpletalk hello.simp
```

Useful variations:

| Command | What it does |
|---|---|
| `simpletalk hello.simp` | runs the program |
| `simpletalk --explain hello.simp` | describes the program in plain English, without running it |
| `simpletalk --trace hello.simp` | runs it, showing each line just before it runs |
| `simpletalk --check hello.simp` | looks for mistakes without running |
| `simpletalk` | interactive mode: type a line, see the result straight away |

Each time you open a new terminal, go back into the folder and activate the environment again with `source .venv/bin/activate`.

## In VS Code

Install the extension from the repository:

```bash
code --install-extension editors/vscode/simpletalk-2.3.1.vsix
```

Then reload VS Code (Ctrl+Shift+P → *Reload Window*) and open a `.simp` file. You get:

- **F5** or the **▶ button** to run the file in VS Code's terminal,
- the **📖 button** to explain it,
- mistakes **underlined in red** when you save,
- colours, auto-indent, and snippets: type `loop` and press Tab.

## The two layout rules

Before you write more, these are the only layout rules in SimpleTalk:

1. **One instruction per line.** Indenting the lines inside a block is optional, but it makes programs much easier to read.
2. **A block ends with a line holding just a dot.** `when`, `loop`, `fn`, `try`, `pick` and `task` all start blocks.

```simp
loop 2
    out "inside the loop"
.
out "after the loop"
```

```output
inside the loop
inside the loop
after the loop
```

Comments start with two semicolons. SimpleTalk ignores everything after them on that line.

```simp
;; This whole line is a note for people reading the program.
out "Hi"   ;; and this is a note at the end of a line
```

```output
Hi
```
