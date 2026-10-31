# SimpleTalk for VS Code

Support for the [SimpleTalk](https://github.com/bicky21/SimpleTalk) programming language in `.simp` files:

- **Run**: press **F5**, or the ▶ button at the top right of the editor. The program runs in VS Code's terminal, so questions from `in` and Ctrl+C work as usual.
- **Explain** (📖 button): the program described line by line in plain English.
- **Trace** (in the ▶ menu or right-click): see each line just before it runs.
- **Mistakes underlined in red** when you open or save a file, with the fix in the tooltip.

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

Download `simpletalk-2.3.1.vsix` from the repository's `editors/vscode` folder, then either:

- In VS Code: **Extensions** view → `...` menu → **Install from VSIX...**, or
- In a terminal: `code --install-extension simpletalk-2.3.1.vsix`

Then run **Developer: Reload Window** (Ctrl+Shift+P).

## Where it finds SimpleTalk

The extension looks for a `.venv` or `venv` folder in your project (and the folders above the file), then for `simpletalk` on your PATH. To use a different one, set **Settings → SimpleTalk: Command**, for example `/home/me/SimpleTalk/.venv/bin/simpletalk`.

Underlining mistakes needs SimpleTalk 2.3.1 or newer (`simpletalk --version`).
