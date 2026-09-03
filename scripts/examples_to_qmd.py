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

Why the transform exists
------------------------
``marimo export md --flavor qmd`` does not currently produce output the
quarto-marimo engine extension (>= 0.4) consumes, so we rewrite it:

1. **Frontmatter.** marimo writes the PEP 723 script metadata under a ``header:``
   key; the extension reads it from ``pyproject:`` (see
   ``_extensions/marimo-team/marimo/python/extract.py``). ``marimo-version`` is
   dropped.

2. **Cell fences.** marimo exports ``` ```{marimo .python} ``` (engine ``marimo``,
   class ``.python``); the extension consumes ``` ```{python .marimo} ```
   (engine ``python``, class ``.marimo``) — the language token and class are
   swapped, so marimo's form renders zero islands. We rewrite to the extension's
   form, and emit ``engine: marimo`` in the frontmatter because quarto-marimo
   >= 0.5 no longer claims files by scanning for fences. (Bug reports:
   ``research/issues/``.)

3. **Code display.** A ``{python .marimo}`` island hides its code by default, and
   ``#| echo: true`` also shows the interactive *editor*, which we do not want on
   a docs page. So we render the code ourselves as a normal, read-only
   ``` ```python ``` block:

   - **visible cell** -> a ``` ```python ``` block *above* the island (code, then
     the island's output);
   - **hidden cell** (``hide_code="true"``) -> the island (output only) followed
     by a collapsible ``<details>`` with the code (``#| code-fold`` is a no-op on
     islands).

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
# appending its GitHub path to molab.marimo.io/github/. The badge only resolves
# once the .py is pushed to this branch, so it goes live when the docs branch merges.
GITHUB_SLUG = "bedrock-engineer/symeval"
GITHUB_BRANCH = "main"
BADGE_IMG = "https://marimo.io/molab-shield.svg"

# Acronyms that should stay uppercase when a snake_case stem is prettified into
# a page title. "getting_started" -> "Getting started"; the rest word-for-word.
_ACRONYMS = {"hss": "HSS"}

# One marimo-exported code cell: ```{marimo .python}``` or the hidden-code
# variant ```{marimo .python hide_code="true"}```, capturing the cell body.
_CELL_RE = re.compile(
    r'^```\{marimo \.python(?P<hide> hide_code="true")?\}[ \t]*\n'
    r"(?P<code>.*?)\n"
    r"```[ \t]*$",
    re.DOTALL | re.MULTILINE,
)


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
    """The molab URL that opens ``examples/<name>.py`` from GitHub.

    The trailing ``/wasm`` opens the notebook in the browser-only WASM
    sandbox rather than a cloud-backed molab session.
    """
    return f"https://molab.marimo.io/github/{GITHUB_SLUG}/blob/{GITHUB_BRANCH}/examples/{name}.py/wasm"


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


def _render_cell(match: re.Match[str]) -> str:
    """Turn one marimo-exported cell into a quarto-marimo island + code display."""
    code = match.group("code")
    hidden = match.group("hide") is not None
    island = f"```{{python .marimo}}\n{code}\n```"
    display = f"```python\n{code}\n```"
    if hidden:
        # Hidden cell: collapsible code above, island's output below (mirrors the
        # visible case). The island's own `#| code-fold` does nothing.
        return (
            "<details>\n<summary>Show code</summary>\n\n"
            f"{display}\n\n"
            "</details>\n\n"
            f"{island}"
        )
    # Visible cell: read-only code block above, island (output) below. We avoid
    # `#| echo: true` because it also renders the interactive editor.
    return f"{display}\n\n{island}"


def transform_cells(body: str) -> str:
    """Rewrite every marimo-exported cell into island + read-only-code form."""
    return _CELL_RE.sub(_render_cell, body)


# The piston JS editor (`mo.ui.code_editor`) only earns its place in the live
# notebook. On the docs page the islands runtime renders the editor twice (it
# re-renders the cell output without removing the static snapshot; see
# research/issues/marimo--islands-duplicate-code-editor.md), so drop the cell
# and point the piston iframe at the editor's initial value, which stays on
# the page. It remains in the source notebooks (symeval_mo.py / getting_started.py).
def strip_js_editor(body: str) -> str:
    """Remove the piston JS-editor cell; docs use its initial value directly."""

    def _drop(match: re.Match[str]) -> str:
        if "piston_js_editor = mo.ui.code_editor" in match.group("code"):
            return ""
        return match.group(0)

    body = _CELL_RE.sub(_drop, body)
    return body.replace("piston_js_editor.value", "initial_piston_js_str")


def build_page(name: str, exported: str) -> str:
    """Assemble the final ``.qmd`` from marimo's export of ``examples/<name>.py``."""
    front, body = split_frontmatter(exported)
    header = extract_header_block(front)
    pyproject = "\n".join(f"  {line}" for line in header.splitlines())

    # quarto-marimo >= 0.5 no longer claims files by scanning for marimo
    # fences; without this the {python .marimo} cells render as literal text.
    frontmatter = [f"title: {pretty_title(name)}", "engine: marimo"]
    if pyproject:
        frontmatter.append("pyproject: |")
        frontmatter.append(pyproject)

    # HTML element (not the ![]() markdown badge) at both the top and the bottom,
    # so a reader can jump to the live notebook from either end of the page.
    badge = f'<a href="{molab_url(name)}"><img src="{BADGE_IMG}" alt="Open in molab"></a>'
    body_md = transform_cells(strip_js_editor(body)).strip("\n")

    return (
        "---\n"
        + "\n".join(frontmatter)
        + "\n---\n\n"
        + badge
        + "\n\n"
        + body_md
        + "\n\n"
        + badge
        + "\n"
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
