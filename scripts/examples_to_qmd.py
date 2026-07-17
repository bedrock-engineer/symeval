# /// script
# requires-python = ">=3.12"
# dependencies = [
#     "marimo",
# ]
# ///
"""Render the ``examples/*.py`` marimo notebooks to Quarto ``docs/examples/*.qmd``.

Each example notebook becomes one documentation page. The pipeline is:

    examples/<name>.py  --marimo export-->  (marimo-flavoured qmd)  --transform-->
    docs/<name-kebab>.qmd            (primary pages, e.g. getting_started)
    docs/examples/<name-kebab>.qmd   (worked-examples gallery)

Primary pages (``PRIMARY_PAGES``) render to the docs root; the rest land in the
``docs/examples/`` gallery.

Two transforms turn marimo's export into a page the quarto-marimo extension
(>= 0.4.x) actually renders as reactive islands:

1. **Cell fences.** marimo exports ``` ```{marimo .python} ``` blocks, which the
   current extension treats as a *deprecated* form and silently hands to the
   Jupyter engine (no islands, no output). The extension's live syntax is
   ``` ```python {.marimo} ```. A hidden-code cell (``hide_code="true"``) maps to
   Quarto's ``#| echo: false`` cell option.

2. **Dependencies.** marimo exports its PEP 723 script metadata under a
   ``header:`` frontmatter key. The extension reads dependencies from a
   ``pyproject:`` key instead (see ``_extensions/marimo-team/marimo/extract.py``),
   so the block is re-keyed. The ``marimo-version`` key is dropped.

The ``.py`` files stay the single source of truth (edit those, or the
``symeval_mo.py`` column behind ``getting_started.py``, then regenerate); the
``.qmd`` files are build artifacts and should not be hand-edited.

File names are snake_case (Python convention) on the ``.py`` side and kebab-case
(web-URL convention) on the ``.qmd`` side: ``getting_started.py`` ->
``getting-started.qmd`` -> ``/examples/getting-started.html``.

Run it with uv so the inline dependency metadata above provisions marimo::

    uv run scripts/examples_to_qmd.py
"""

from __future__ import annotations

import re
import subprocess
import sys
import tempfile
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
EXAMPLES = REPO_ROOT / "examples"
DOCS = REPO_ROOT / "docs"
EXAMPLES_OUT = DOCS / "examples"

# Notebooks that are primary pages rather than gallery examples render to the
# docs root (getting_started -> docs/getting-started.qmd). Everything else lands
# in docs/examples/ (the worked-examples gallery).
PRIMARY_PAGES = {"getting_started"}

# The molab "Open in <name>" badge opens a GitHub-hosted notebook in molab by
# appending its GitHub blob URL to molab.marimo.io. The badge only resolves once
# the .py is pushed to this branch, so it goes live when the docs branch merges.
GITHUB_SLUG = "bedrock-engineer/symeval"
GITHUB_BRANCH = "main"
BADGE_IMG = "https://img.shields.io/badge/Open%20in-molab-63805e"

# Acronyms that should stay uppercase when a snake_case stem is prettified into
# a page title. "getting_started" -> "Getting started"; the rest word-for-word.
_ACRONYMS = {"hss": "HSS"}


def pretty_title(stem: str) -> str:
    """Turn a snake_case file stem into a human page title."""
    words = stem.split("_")
    out = []
    for i, word in enumerate(words):
        if word in _ACRONYMS:
            out.append(_ACRONYMS[word])
        elif i == 0:
            out.append(word.capitalize())
        else:
            out.append(word)
    return " ".join(out)


def molab_url(name: str) -> str:
    """The molab URL that opens ``examples/<name>.py`` from GitHub."""
    blob = f"https://github.com/{GITHUB_SLUG}/blob/{GITHUB_BRANCH}/examples/{name}.py"
    return f"https://molab.marimo.io/{blob}"


def split_frontmatter(text: str) -> tuple[list[str], str]:
    """Split a ``---`` delimited YAML frontmatter from the document body."""
    if not text.startswith("---\n"):
        return [], text
    end = text.index("\n---\n", 4)
    return text[4:end].splitlines(), text[end + 5 :]


def extract_header_block(front: list[str]) -> str:
    """Pull the PEP 723 block out of marimo's ``header: |-`` frontmatter value."""
    try:
        start = next(i for i, line in enumerate(front) if re.match(r"header:\s*\|", line))
    except StopIteration:
        return ""
    body = []
    for line in front[start + 1 :]:
        if line and not line[0].isspace():
            break  # dedented => next top-level key
        body.append(line)
    # Strip the common leading indent marimo added under the block scalar.
    indents = [len(l) - len(l.lstrip()) for l in body if l.strip()]
    pad = min(indents) if indents else 0
    return "\n".join(l[pad:] for l in body).strip("\n")


def transform_cells(body: str) -> str:
    """Rewrite marimo's deprecated cell fences into the extension's live syntax."""
    body = re.sub(
        r'^```\{marimo \.python hide_code="true"\}[ \t]*$',
        "```python {.marimo}\n#| echo: false",
        body,
        flags=re.MULTILINE,
    )
    body = re.sub(
        r"^```\{marimo \.python\}[ \t]*$",
        "```python {.marimo}",
        body,
        flags=re.MULTILINE,
    )
    return body


def build_page(name: str, exported: str) -> str:
    """Assemble the final ``.qmd`` from marimo's export of ``examples/<name>.py``."""
    front, body = split_frontmatter(exported)
    header = extract_header_block(front)
    pyproject = "\n".join(f"  {line}" for line in header.splitlines())

    frontmatter = [f"title: {pretty_title(name)}"]
    if pyproject:
        frontmatter.append("pyproject: |")
        frontmatter.append(pyproject)

    badge = f"[![Open in molab]({BADGE_IMG})]({molab_url(name)})\n"

    return (
        "---\n"
        + "\n".join(frontmatter)
        + "\n---\n\n"
        + badge
        + "\n"
        + transform_cells(body).lstrip("\n")
    )


def output_path(stem: str) -> Path:
    """Where the ``.qmd`` for ``examples/<stem>.py`` is written."""
    directory = DOCS if stem in PRIMARY_PAGES else EXAMPLES_OUT
    return directory / f"{stem.replace('_', '-')}.qmd"


def main() -> None:
    notebooks = sorted(EXAMPLES.glob("*.py"))
    if not notebooks:
        raise SystemExit(f"No example notebooks found in {EXAMPLES}")

    for nb in notebooks:
        with tempfile.NamedTemporaryFile("w+", suffix=".qmd", delete=False) as tmp:
            tmp_path = Path(tmp.name)
        subprocess.run(
            [sys.executable, "-m", "marimo", "export", "md", "--flavor", "qmd",
             str(nb), "-o", str(tmp_path), "-f"],
            check=True,
        )
        page = build_page(nb.stem, tmp_path.read_text())
        tmp_path.unlink(missing_ok=True)

        out = output_path(nb.stem)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(page)
        print(f"Wrote {out.relative_to(REPO_ROOT)}")


if __name__ == "__main__":
    main()
