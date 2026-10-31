"""SimpleTalk - a friendly, simple programming language written in Python.

Use it from Python:

    from simpletalk import run
    run('out "Hello!"')
"""

from .errors import RuntimeProblem, SimpleTalkError, SyntaxProblem
from .interpreter import Interpreter
from .parser import parse

__version__ = "2.3.1"
__all__ = ["run", "parse", "Interpreter", "SimpleTalkError", "SyntaxProblem",
           "RuntimeProblem", "__version__"]


def run(source, output=None, input_fn=None, interpreter=None):
    """Run SimpleTalk source code. Raises SimpleTalkError on problems."""
    program = parse(source)
    interp = interpreter or Interpreter(output=output, input_fn=input_fn)
    interp.run(program)
    return interp
