// SimpleTalk playground engine.
//
// Runs the real SimpleTalk interpreter (the same Python code as the
// `simpletalk` command) inside Pyodide, in a Web Worker so the page never
// freezes. The page stops a runaway program by ending this worker and
// starting a fresh one.

// Pyodide comes from jsDelivr unless the page says otherwise
// (?pyodide=/my/copy/ lets a school host everything itself, even offline).
const PYODIDE = new URL(self.location).searchParams.get("pyodide") ||
  "https://cdn.jsdelivr.net/npm/pyodide@314.0.7/";
// This is a module worker: current Pyodide no longer runs in classic workers.

const HOME = "/home/pyodide";
let pyodide = null;
let runProgram = null;

function send(message) {
  self.postMessage(message);
}

async function start() {
  try {
    send({ type: "status", text: "Downloading the engine (about 10 MB, only the first time)..." });
    const { loadPyodide } = await import(PYODIDE + "pyodide.mjs");
    pyodide = await loadPyodide({ indexURL: PYODIDE });

    send({ type: "status", text: "Loading SimpleTalk..." });
    const bundle = await (await fetch("bundle.json", { cache: "no-cache" })).json();
    for (const [path, text] of Object.entries(bundle.engine)) {
      const full = `${HOME}/${path}`;
      pyodide.FS.mkdirTree(full.slice(0, full.lastIndexOf("/")));
      pyodide.FS.writeFile(full, text);
    }
    // Library files the examples `use` live next to the program.
    for (const [path, text] of Object.entries(bundle.library)) {
      const full = `${HOME}/play/${path}`;
      pyodide.FS.mkdirTree(full.slice(0, full.lastIndexOf("/")));
      pyodide.FS.writeFile(full, text);
    }
    pyodide.FS.mkdirTree(`${HOME}/play`);

    pyodide.runPython(PYTHON);
    runProgram = pyodide.globals.get("run_program");
    const version = pyodide.runPython("__version__");
    send({ type: "ready", version });
  } catch (err) {
    send({ type: "fatal", text: "The engine could not start: " + err });
  }
}

const PYTHON = `
import json, os, sys, time
sys.path.insert(0, "${HOME}")
from js import postMessage
from simpletalk import Interpreter, SimpleTalkError, __version__, parse
from simpletalk.errors import RuntimeProblem
from simpletalk.explain import explain

PROGRAM = "${HOME}/play/main.simp"
MEMORY = "${HOME}/play/main.memory.json"
MAX_LINES = 20000


def post(kind, **fields):
    fields["type"] = kind
    postMessage(json.dumps(fields))


def run_program(code, answers_json, memory_json, mode):
    answers = iter(json.loads(answers_json))
    with open(PROGRAM, "w", encoding="utf-8") as f:
        f.write(code)
    if memory_json:
        with open(MEMORY, "w", encoding="utf-8") as f:
            f.write(memory_json)
    elif os.path.exists(MEMORY):
        os.remove(MEMORY)

    buffer, lines, last = [], [0], [time.monotonic()]

    def flush():
        if buffer:
            post("out", text="\\n".join(buffer))
            buffer.clear()
        last[0] = time.monotonic()

    def output(text):
        lines[0] += 1
        if lines[0] > MAX_LINES:
            raise RuntimeProblem(f"The program printed more than {MAX_LINES:,} lines, so the playground stopped it.",
                                 hint="Print less inside loops, or run it on your computer with: simpletalk main.simp")
        buffer.append(text)
        if len(buffer) >= 200 or time.monotonic() - last[0] > 0.05:
            flush()

    def answer(prompt=""):
        try:
            value = next(answers)
        except StopIteration:
            output(prompt + "(no more answers)")
            raise EOFError
        output(prompt + value)            # looks like a terminal: question, then the answer
        return value

    started = time.monotonic()
    tests = 0
    try:
        program = parse(code)
        if mode == "explain":
            output(explain(program))
        else:
            interp = Interpreter(output=output, input_fn=answer, program_path=PROGRAM)
            interp.source, interp.filename = code, "main.simp"
            try:
                interp.run(program)
            finally:
                tests = interp.tests_passed
        flush()
        if tests:
            post("note", text=f"[test] {tests} test{'s' if tests != 1 else ''} passed.")
    except SimpleTalkError as err:
        flush()
        if tests:
            post("note", text=f"[test] {tests} test{'s' if tests != 1 else ''} passed.")
        post("problem", text=err.pretty(code, "main.simp"))
    except RecursionError:
        flush()
        post("problem", text="Oops! The program went too deep (too many nested calls).")
    memory = None
    if os.path.exists(MEMORY):
        with open(MEMORY, encoding="utf-8") as f:
            memory = f.read()
    post("done", ms=round((time.monotonic() - started) * 1000), memory=memory)
`;

self.onmessage = (event) => {
  const msg = event.data;
  if (msg.type === "run" && runProgram) {
    try {
      runProgram(msg.code, JSON.stringify(msg.answers || []), msg.memory || "", msg.mode || "run");
    } catch (err) {
      send({ type: "fatal", text: "Something went wrong inside the playground: " + err });
    }
  }
};

// Python posts JSON text; turn it into objects for the page.
const rawPost = self.postMessage.bind(self);
self.postMessage = (m) => rawPost(typeof m === "string" ? JSON.parse(m) : m);

start();
