"""Build the SimpleTalk manual (docs/manual/*.md) into a website.

    python docs/build_manual.py              # writes _site/manual/
    python playground/build.py               # builds the playground and the manual

Needs the `markdown` package (pip install markdown); the GitHub Pages workflow
installs it. Code blocks get SimpleTalk colours and a "Try it" button that
opens the example in the playground.
"""

import base64
import html
import json
import pathlib
import re
import sys

import markdown

ROOT = pathlib.Path(__file__).resolve().parent.parent
SOURCE = ROOT / "docs" / "manual"
PLAYGROUND_URL = "https://bicky21.github.io/SimpleTalk/"
BLOCK = re.compile(r"^```(\w+)([^\n]*)\n(.*?)^```[ \t]*$", re.S | re.M)

GROUPS = [
    ("Learning the language", ["01", "02", "03", "04", "05", "06", "07"]),
    ("Going further", ["08", "09", "10", "11", "12", "13", "14"]),
    ("Putting it together", ["15", "16", "17"]),
]

# ------------------------------------------------------------------ highlighting
KEYWORDS = ("when|else|loop|while|stop|skip|ret|try|fail|oops|pick|is|await|let|up|out|in|"
            "add|del|watch|test|use|keep|fn|task|and|or|not|has|mod")
BUILTINS = ("len|num|isnum|txt|type|round|abs|sqrt|pow|rand|min|max|sum|upper|lower|trim|swap|"
            "split|join|sort|rev|copy|wait|keys|values|read|write|load|save|exists")
TOKENS = re.compile(rf"""
    (?P<com>;;[^\n]*)
  | (?P<dot>^[ \t]*\.(?=[ \t]*(?:;;|$)))
  | (?P<str>"(?:[^"\\\n]|\\.)*"?|'(?:[^'\\\n]|\\.)*'?)
  | (?P<def>(?<=\bfn\s)(?!\s)[A-Za-z_]\w*(?=[ \t]+\w|[ \t]*$)|(?<=\btask\s)[A-Za-z_]\w*)
  | (?P<kw>\b(?:{KEYWORDS})\b|\|[ \t]*(?:only|each)\b)
  | (?P<atom>\b(?:true|false|none)\b)
  | (?P<fn>\b(?:{BUILTINS})(?=\())
  | (?P<it>\bit\b)
  | (?P<num>\b\d[\d_]*(?:\.\d[\d_]*)?)
  | (?P<op>\.\.|->|!=|<=|>=|[=<>+\-*/|])
""", re.M | re.X)


def highlight(code):
    out, pos = [], 0
    for m in TOKENS.finditer(code):
        out.append(html.escape(code[pos:m.start()]))
        out.append(f'<span class="t-{m.lastgroup}">{html.escape(m.group(0))}</span>')
        pos = m.end()
    out.append(html.escape(code[pos:]))
    return "".join(out)


def playground_link(code, options):
    def b64(text):
        return base64.urlsafe_b64encode(text.encode("utf-8")).decode().rstrip("=")
    link = f"../#code={b64(code.rstrip())}"
    answers = re.search(r"input=(\S*)", options)
    if answers:
        link += "&answers=" + b64("\n".join(answers.group(1).split("|")))
    return link


# ------------------------------------------------------------------ pages
class Page:
    def __init__(self, path):
        self.path = path
        self.stem = path.stem
        self.number = self.stem[:2]
        self.url = "index.html" if self.number == "00" else f"{self.stem}.html"
        self.text = path.read_text(encoding="utf-8")
        self.title = re.search(r"^# (.+)$", self.text, re.M).group(1).strip()


def render_blocks(text):
    """Replace SimpleTalk and output blocks with finished HTML before markdown runs."""
    pieces, pos = [], 0
    blocks = list(BLOCK.finditer(text))
    for i, m in enumerate(blocks):
        kind, options, body = m.group(1), m.group(2).strip(), m.group(3)
        if kind not in ("simp", "output"):
            continue
        pieces.append(text[pos:m.start()])
        if kind == "simp":
            label = "SimpleTalk"
            if "error" in options:
                label = "SimpleTalk · stops with a problem"
            button = f'<a class="try" href="{playground_link(body, options)}">Try it</a>'
            if "input=" in options:
                answers = ", ".join(re.search(r"input=(\S*)", options).group(1).split("|"))
                button = (f'<span class="answers">answers: {html.escape(answers)}</span>' + button)
            pieces.append(
                f'\n<figure class="code"><figcaption><span>{label}</span>{button}</figcaption>'
                f'<pre><code>{highlight(body.rstrip())}</code></pre></figure>\n')
        else:
            problem = body.lstrip().startswith("Oops!")
            cls = "output problem" if problem else "output"
            pieces.append(
                f'\n<figure class="{cls}"><figcaption>{"Message" if problem else "Output"}</figcaption>'
                f'<pre>{html.escape(body.rstrip())}</pre></figure>\n')
        pos = m.end()
    pieces.append(text[pos:])
    return "".join(pieces)


def to_html(page):
    text = re.sub(r"^# .+\n", "", page.text, count=1)
    # GitHub needs \| for a pipe inside a table cell; this Markdown library doesn't
    text = "\n".join(line.replace("\\|", "|") if line.lstrip().startswith("|") else line
                     for line in text.split("\n"))
    text = render_blocks(text)
    # links: chapter .md files -> .html, the playground -> relative (works when self-hosted)
    text = re.sub(r"\]\((\d\d-[a-z-]+)\.md(#[^)]*)?\)",
                  lambda m: f"]({'index' if m.group(1).startswith('00') else m.group(1)}.html{m.group(2) or ''})", text)
    text = text.replace(f"]({PLAYGROUND_URL})", "](../)")
    md = markdown.Markdown(extensions=["tables", "fenced_code", "toc", "sane_lists"],
                           extension_configs={"toc": {"permalink": False}})
    body = md.convert(text)
    headings = [(t["id"], t["name"]) for t in md.toc_tokens for t in [t] + t.get("children", [])
                if t.get("level") == 2]
    return body, headings


def plain(text):
    text = BLOCK.sub(" ", text)
    text = re.sub(r"[`*#|>\[\]()_]", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def nav_html(pages, current):
    by_number = {p.number: p for p in pages}
    parts = [f'<a class="home{" current" if current.number == "00" else ""}" href="index.html">Manual home</a>']
    for title, numbers in GROUPS:
        parts.append(f'<p class="group">{html.escape(title)}</p><ol>')
        for n in numbers:
            p = by_number.get(n)
            if p:
                cur = ' class="current" aria-current="page"' if p is current else ""
                parts.append(f'<li><a{cur} href="{p.url}"><span class="n">{int(n)}</span>{html.escape(p.title)}</a></li>')
        parts.append("</ol>")
    return "\n".join(parts)


def build(out_dir):
    out_dir = pathlib.Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    pages = [Page(p) for p in sorted(SOURCE.glob("*.md"))]
    template = (ROOT / "docs" / "manual_template.html").read_text(encoding="utf-8")
    search = []
    for i, page in enumerate(pages):
        body, headings = to_html(page)
        prev_page = pages[i - 1] if i > 0 else None
        next_page = pages[i + 1] if i + 1 < len(pages) else None
        pager = '<nav class="pager" aria-label="Previous and next chapter">'
        pager += (f'<a class="prev" href="{prev_page.url}"><small>Previous</small>{html.escape(prev_page.title)}</a>'
                  if prev_page else "<span></span>")
        pager += (f'<a class="next" href="{next_page.url}"><small>Next</small>{html.escape(next_page.title)}</a>'
                  if next_page else "<span></span>")
        pager += "</nav>"
        toc = ""
        if len(headings) > 1:
            toc = '<nav class="toc" aria-label="On this page"><p>On this page</p><ul>' + "".join(
                f'<li><a href="#{hid}">{name}</a></li>' for hid, name in headings) + "</ul></nav>"
        chapter = "" if page.number == "00" else f'<p class="chapter">Chapter {int(page.number)}</p>'
        source = f"https://github.com/bicky21/SimpleTalk/blob/master/docs/manual/{page.path.name}"
        filled = (template
                  .replace("{{title}}", html.escape(page.title))
                  .replace("{{nav}}", nav_html(pages, page))
                  .replace("{{chapter}}", chapter)
                  .replace("{{heading}}", html.escape(page.title))
                  .replace("{{body}}", body)
                  .replace("{{toc}}", toc)
                  .replace("{{pager}}", pager)
                  .replace("{{source}}", source))
        (out_dir / page.url).write_text(filled, encoding="utf-8")
        search.append({"url": page.url, "title": page.title, "text": plain(page.text)})
    (out_dir / "search.json").write_text(json.dumps(search), encoding="utf-8")
    return len(pages)


if __name__ == "__main__":
    target = pathlib.Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT / "_site" / "manual"
    print(f"Built {build(target)} manual pages into {target}")
