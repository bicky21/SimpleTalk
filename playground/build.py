"""Build the playground website into _site/ (used by GitHub Pages).

    python playground/build.py            # then: python -m http.server -d _site

bundle.json holds the SimpleTalk engine (the Python files), the example
programs for the Examples menu, and library files the examples `use`.
"""

import json
import pathlib
import re
import shutil

ROOT = pathlib.Path(__file__).resolve().parent.parent
SITE = ROOT / "_site"

# Examples that need answers typed in get sample answers in the playground.
ANSWERS = {
    "07_guess_the_number.simp": "25\nten\n10\n15\n5\n12\n8\n3\n18\n1\n2\n4\n6\n7\n9\n11\n13\n14\n16\n17\n19\n20",
    "09_superpowers.simp": "twenty\n20\nmaybe\nyes",
}


def title(path):
    name = re.sub(r"^\d+_", "", path.stem).replace("_", " ")
    return f"{path.stem[:2]}. {name.capitalize()}" if path.stem[:2].isdigit() else name


def main():
    if SITE.exists():
        shutil.rmtree(SITE)
    SITE.mkdir()
    engine = {f"simpletalk/{p.name}": p.read_text(encoding="utf-8")
              for p in sorted((ROOT / "simpletalk").glob("*.py"))}
    examples = [{"file": p.name, "title": title(p), "code": p.read_text(encoding="utf-8"),
                 "answers": ANSWERS.get(p.name, "")}
                for p in sorted((ROOT / "examples").glob("*.simp"))]
    library = {f"lib/{p.name}": p.read_text(encoding="utf-8")
               for p in sorted((ROOT / "examples" / "lib").glob("*.simp"))}
    (SITE / "bundle.json").write_text(json.dumps(
        {"engine": engine, "examples": examples, "library": library}), encoding="utf-8")
    for name in ("index.html", "worker.js"):
        shutil.copy(ROOT / "playground" / name, SITE / name)
    (SITE / ".nojekyll").write_text("")
    print(f"Built {SITE} with {len(engine)} engine files and {len(examples)} examples.")


if __name__ == "__main__":
    main()
