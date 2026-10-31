// SimpleTalk for VS Code: Run (▶ button and F5), Explain, Trace, and red
// squiggles under mistakes when a file is saved.
//
// Programs run in VS Code's terminal with the `simpletalk` command, so `in`
// (questions to the user) and Ctrl+C work exactly as they do in a terminal.

const vscode = require("vscode");
const cp = require("child_process");
const fs = require("fs");
const path = require("path");

const isWindows = process.platform === "win32";
let diagnostics;
let terminal;
let warnedMissing = false;

// ------------------------------------------------------------------ finding simpletalk
/** The command to run: the user's setting, a project .venv, or `simpletalk` on PATH. */
function findCommand(fileDir) {
  const setting = vscode.workspace.getConfiguration("simpletalk").get("command");
  if (setting && setting.trim()) return setting.trim();
  const candidates = isWindows
    ? [[".venv", "Scripts", "simpletalk.exe"], ["venv", "Scripts", "simpletalk.exe"]]
    : [[".venv", "bin", "simpletalk"], ["venv", "bin", "simpletalk"]];
  let dir = fileDir;
  for (let i = 0; i < 12 && dir; i++) {
    for (const parts of candidates) {
      const p = path.join(dir, ...parts);
      if (fs.existsSync(p)) return p;
    }
    const parent = path.dirname(dir);
    if (parent === dir) break;
    dir = parent;
  }
  return "simpletalk";
}

function quote(arg) {
  if (isWindows) return `"${arg.replace(/"/g, '""')}"`;
  return `'${arg.replace(/'/g, `'\\''`)}'`;
}

// ------------------------------------------------------------------ running
async function fileToRun(uri) {
  let doc;
  if (uri) {
    doc = await vscode.workspace.openTextDocument(uri);
  } else if (vscode.window.activeTextEditor) {
    doc = vscode.window.activeTextEditor.document;
  }
  if (!doc || doc.languageId !== "simpletalk") {
    vscode.window.showWarningMessage("Open a SimpleTalk (.simp) file first.");
    return undefined;
  }
  if (doc.isUntitled) {
    vscode.window.showWarningMessage("Save this program as a .simp file first, then run it.");
    return undefined;
  }
  if (doc.isDirty) await doc.save();
  return doc.uri.fsPath;
}

function runInTerminal(file, flag) {
  const dir = path.dirname(file);
  const command = findCommand(dir);
  if (!terminal || terminal.exitStatus !== undefined) {
    terminal = vscode.window.createTerminal({ name: "SimpleTalk", cwd: dir });
  }
  terminal.show(true);
  const args = [flag, quote(file)].filter(Boolean).join(" ");
  const prefix = isWindows ? "& " : "";          // PowerShell needs & to run a quoted path
  terminal.sendText(`${prefix}${quote(command)} ${args}`);
}

async function run(flag, uri) {
  const file = await fileToRun(uri);
  if (file) runInTerminal(file, flag);
}

// ------------------------------------------------------------------ squiggles
function check(doc) {
  if (doc.languageId !== "simpletalk" || doc.isUntitled) return;
  if (!vscode.workspace.getConfiguration("simpletalk").get("checkOnSave", true)) {
    diagnostics.delete(doc.uri);
    return;
  }
  const file = doc.uri.fsPath;
  const command = findCommand(path.dirname(file));
  cp.execFile(command, ["--check", "--json", file], { cwd: path.dirname(file), timeout: 10000 },
    (error, stdout) => {
      if (error && error.code === "ENOENT") {
        if (!warnedMissing) {
          warnedMissing = true;
          vscode.window.showWarningMessage(
            "The `simpletalk` command wasn't found, so mistakes can't be underlined. " +
            "Install SimpleTalk (pip install -e .) or set 'simpletalk.command' in Settings.");
        }
        return;
      }
      const result = parseCheck(stdout);
      if (!result) return;                                  // older SimpleTalk without --json
      if (result.ok) {
        diagnostics.delete(doc.uri);
        return;
      }
      diagnostics.set(doc.uri, [toDiagnostic(doc, result)]);
    });
}

function parseCheck(stdout) {
  const last = String(stdout || "").trim().split(/\r?\n/).pop();
  try {
    const result = JSON.parse(last);
    return typeof result === "object" && result && "ok" in result ? result : undefined;
  } catch {
    return undefined;
  }
}

function toDiagnostic(doc, result) {
  const line = Math.min(Math.max((result.line || 1) - 1, 0), Math.max(doc.lineCount - 1, 0));
  const text = doc.lineAt(line).text;
  const start = Math.min(Math.max((result.column || 1) - 1, 0), text.length);
  const word = text.slice(start).match(/^[A-Za-z_][A-Za-z0-9_]*|^\S/);
  const end = word ? start + word[0].length : text.length;
  const range = new vscode.Range(line, start, line, Math.max(end, start + 1));
  const message = result.hint ? `${result.message}\nHint: ${result.hint}` : result.message;
  const d = new vscode.Diagnostic(range, message, vscode.DiagnosticSeverity.Error);
  d.source = "SimpleTalk";
  return d;
}

// ------------------------------------------------------------------ F5
// F5 (and Ctrl+F5) run the current file in the terminal. There is no step-by-step
// debugger, so after starting the program we cancel the debug session itself.
const debugProvider = {
  provideDebugConfigurations() {
    return [{ type: "simpletalk", request: "launch", name: "Run SimpleTalk file", program: "${file}" }];
  },
  resolveDebugConfiguration(folder, config) {
    if (!config.type && !config.request && !config.name) {
      config = { type: "simpletalk", request: "launch", name: "Run SimpleTalk file", program: "${file}" };
    }
    if (!config.program) config.program = "${file}";
    return config;
  },
  async resolveDebugConfigurationWithSubstitutedVariables(folder, config) {
    const program = config.program && !config.program.includes("${") ? vscode.Uri.file(config.program) : undefined;
    await run(config.trace ? "--trace" : "", program);
    return undefined;          // nothing to debug: the program is already running in the terminal
  },
};

// ------------------------------------------------------------------ setup
function activate(context) {
  diagnostics = vscode.languages.createDiagnosticCollection("simpletalk");
  context.subscriptions.push(
    diagnostics,
    vscode.commands.registerCommand("simpletalk.run", (uri) => run("", uri)),
    vscode.commands.registerCommand("simpletalk.explain", (uri) => run("--explain", uri)),
    vscode.commands.registerCommand("simpletalk.trace", (uri) => run("--trace", uri)),
    vscode.debug.registerDebugConfigurationProvider("simpletalk", debugProvider),
    vscode.workspace.onDidSaveTextDocument(check),
    vscode.workspace.onDidOpenTextDocument(check),
    vscode.workspace.onDidCloseTextDocument((doc) => diagnostics.delete(doc.uri)),
    vscode.window.onDidCloseTerminal((t) => { if (t === terminal) terminal = undefined; }),
  );
  vscode.workspace.textDocuments.forEach(check);
}

function deactivate() {}

module.exports = { activate, deactivate, _test: { findCommand, quote, parseCheck, toDiagnostic, debugProvider } };
