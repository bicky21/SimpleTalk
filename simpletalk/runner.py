"""Run SimpleTalk code safely on every computer.

Why this file exists
--------------------
Python 3.10 and older use the operating system's call stack for every
function call, and Windows gives the main thread a small stack (about 1 MB).
A deeply recursive SimpleTalk program could then crash Python itself
("Windows fatal exception: stack overflow") instead of showing a friendly
message.

So programs run in a worker thread that gets its own large stack. The stack
is only *reserved* address space, not memory that is actually used, so this
is cheap even on low-spec machines.

The main thread stays in charge of the keyboard: it reads the answers for
`in` and turns Ctrl+C into a clean stop.
"""

import builtins
import queue
import sys
import threading

# (stack size, recursion limit) to try, largest first. Smaller ones are a
# fallback for systems that refuse a big stack (for example 32-bit Python).
_STACKS = [(256 * 1024 * 1024, 50_000), (64 * 1024 * 1024, 12_000), (16 * 1024 * 1024, 3_000)]

_POLL = 0.1   # seconds; lets Ctrl+C be noticed on Windows while waiting


class _Interrupt:
    """Sent to the worker when the user presses Ctrl+C while it waits for input."""


def run_protected(interp, task):
    """Run `task()` (which uses `interp`) on a big-stack worker thread.

    Returns what `task` returns and re-raises what it raises, exactly as if it
    had been called directly. KeyboardInterrupt (Ctrl+C) stops the program.
    """
    if getattr(threading.current_thread(), "_simpletalk_worker", False):
        return task()                       # already on a worker (nested run)

    events = queue.Queue()
    answers = queue.Queue()
    uses_keyboard = interp.input_fn is builtins.input

    def ask_main_thread(prompt=""):
        events.put(("input", prompt))
        answer = answers.get()
        if isinstance(answer, BaseException):
            raise answer
        if answer is _Interrupt:
            raise KeyboardInterrupt
        return answer

    def work():
        threading.current_thread()._simpletalk_worker = True
        old_input = interp.input_fn
        if uses_keyboard:
            interp.input_fn = ask_main_thread
        try:
            events.put(("done", task(), None))
        except BaseException as err:          # handed back to the main thread
            events.put(("done", None, err))
        finally:
            interp.input_fn = old_input

    thread = _start(work)
    if thread is None:                         # no thread possible: run directly
        return task()

    while True:
        try:
            event = events.get(timeout=_POLL)
        except queue.Empty:
            continue
        except KeyboardInterrupt:
            interp.interrupted = True          # worker stops at its next step
            continue
        if event[0] == "input":
            try:
                answers.put(input(event[1]))
            except EOFError as err:
                answers.put(err)
            except KeyboardInterrupt:
                interp.interrupted = True
                answers.put(_Interrupt)
            continue
        _, result, error = event
        thread.join()
        interp.interrupted = False
        if error is not None:
            raise error
        return result


def _start(target):
    old_size = threading.stack_size()
    old_limit = sys.getrecursionlimit()
    try:
        for size, limit in _STACKS:
            try:
                threading.stack_size(size)
            except (ValueError, RuntimeError):
                continue
            thread = threading.Thread(target=_with_limit(target, limit, old_limit),
                                      name="simpletalk", daemon=True)
            try:
                thread.start()
            except (RuntimeError, MemoryError):
                continue
            return thread
        return None
    finally:
        threading.stack_size(old_size)


def _with_limit(target, limit, old_limit):
    def run():
        # The recursion limit is shared by all threads; raise it only while
        # SimpleTalk code runs, on the thread whose stack can take it.
        sys.setrecursionlimit(max(old_limit, limit))
        try:
            target()
        finally:
            sys.setrecursionlimit(old_limit)
    return run
