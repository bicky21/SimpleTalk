# SimpleTalk for VS Code

Support for the [SimpleTalk](https://github.com/bicky21/SimpleTalk) programming language in `.simp` files:

- **Syntax highlighting**: keywords, text with `{values}` inside, numbers, maps, fields, pipelines and the closing `.` of every block.
- **Snippets**: type a word and press Tab.

  | Type        | You get                          |
  |-------------|----------------------------------|
  | `when`      | a `when` block                   |
  | `whenelse`  | `when` / `else`                  |
  | `loop`      | `loop 3`                         |
  | `loopi`     | `loop i 1..10`                   |
  | `loopeach`  | `loop item items`                |
  | `loopwhile` | `loop while ...`                 |
  | `fn`        | a function with `ret`            |
  | `try`       | `try` / `fail why`               |
  | `pick`      | `pick` / `is` / `else`           |
  | `task`      | a task and its `await`           |
  | `map`, `pipe`, `test` | one-line helpers       |

- **Auto-indent**: lines after `when`, `loop`, `fn`, `try`, `pick`, `task` are indented, and `.` / `else` / `is` / `fail` line up with their block.
- **Comments**: `Ctrl+/` toggles `;;` comments.

## Install

Download `simpletalk-2.3.0.vsix` from the repository's `editors/vscode` folder, then either:

- In VS Code: **Extensions** view → `...` menu → **Install from VSIX...**, or
- In a terminal: `code --install-extension simpletalk-2.3.0.vsix`

## Run a program

Open a terminal in VS Code and run `simpletalk your_program.simp`.
