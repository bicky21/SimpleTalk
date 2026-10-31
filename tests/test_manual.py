"""Every SimpleTalk example in the manual must work, and print what the manual says.

In docs/manual/*.md:

    ```simp                  a program; must run without problems
    ```simp input=20|yes     answers for `in`, separated by |
    ```simp error            the program must stop with a problem
    ```simp files            runs in an empty folder (with examples/lib/), for file examples
    ```simp norun            only checked for mistakes

A ```output block right after a program is compared with what it prints.
"""

import pathlib
import re

import pytest

from simpletalk import Interpreter, SimpleTalkError, parse

MANUAL = pathlib.Path(__file__).parent.parent / "docs" / "manual"
BLOCK = re.compile(r"^```(\w+)([^\n]*)\n(.*?)^```\s*$", re.S | re.M)


def examples():
    for page in sorted(MANUAL.glob("*.md")):
        text = page.read_text(encoding="utf-8")
        blocks = list(BLOCK.finditer(text))
        for i, block in enumerate(blocks):
            if block.group(1) != "simp":
                continue
            options = block.group(2).strip()
            expected = None
            if i + 1 < len(blocks) and blocks[i + 1].group(1) == "output":
                between = text[block.end():blocks[i + 1].start()]
                if not between.strip():
                    expected = blocks[i + 1].group(3).rstrip("\n")
            line = text[:block.start()].count("\n") + 1
            yield pytest.param(block.group(3), options, expected, id=f"{page.stem}:{line}")


def run_example(code, options, folder=None):
    lines = []
    answers = iter(re.search(r"input=(\S*)", options).group(1).split("|")) if "input=" in options else iter(())

    def answer(prompt=""):
        value = next(answers)
        lines.append(prompt + value)          # shown like a terminal: question, then the answer
        return value

    program_path = str(folder / "main.simp") if folder else None
    interp = Interpreter(output=lines.append, input_fn=answer, program_path=program_path)
    try:
        interp.run(parse(code))
    except SimpleTalkError as err:
        return lines, err, interp
    return lines, None, interp


@pytest.mark.parametrize("code, options, expected", list(examples()))
def test_manual_example(code, options, expected, tmp_path):
    if "norun" in options:
        parse(code)
        return
    folder = None
    if "files" in options:
        import shutil
        folder = tmp_path
        shutil.copytree(MANUAL.parent.parent / "examples" / "lib", folder / "lib")
    lines, err, interp = run_example(code, options, folder)
    if "error" in options:
        assert err is not None, "this example should stop with a problem"
        printed = "\n".join(lines + [err.pretty(code)]).rstrip("\n")
    else:
        assert err is None, f"example failed:\n{err.pretty(code) if err else ''}"
        if interp.tests_passed:
            n = interp.tests_passed
            lines.append(f"[test] {n} test{'s' if n != 1 else ''} passed.")
        printed = "\n".join(lines)
    if expected is not None:
        assert printed == expected


def test_manual_has_examples():
    assert len(list(examples())) > 50


def test_manual_site_builds_with_working_links(tmp_path):
    pytest.importorskip("markdown")
    import html
    import importlib.util
    spec = importlib.util.spec_from_file_location("build_manual", MANUAL.parent / "build_manual.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    assert module.build(tmp_path) == len(list(MANUAL.glob("*.md")))
    pages = {p.name: p.read_text(encoding="utf-8") for p in tmp_path.glob("*.html")}
    for name, text in pages.items():
        for href in re.findall(r'href="([^"#]+)(?:#([^"]*))?"', text):
            target, frag = href
            target = html.unescape(target)
            if target.startswith(("http", "../")):
                continue
            assert target in pages, f"{name} links to missing {target}"
            if frag:
                assert f'id="{frag}"' in pages[target], f"{name} links to missing #{frag}"
    assert "Try it" in pages["02-first-steps.html"]
