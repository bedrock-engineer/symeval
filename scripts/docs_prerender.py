# /// script
# requires-python = ">=3.12"
# dependencies = [
#     "marimo",
# ]
# ///
"""The docs site's Quarto ``pre-render:`` hook: notebooks to pages, SymEval style.

quarto-marimo ships the generic step (``quarto_marimo.prerender`` in the
vendored extension under ``docs/_extensions/``): every marimo notebook under
``docs/`` becomes a ``.qmd`` next to it, titled after its opening heading,
showing its code and failing the render on a cell error. This script runs that
step with the page tweaks specific to this repository:

- **Page links.** Under the table of contents, where the other pages show
  Quarto's GitHub links, a notebook page shows its own: "View source" (the
  notebook on GitHub; Quarto's link would point at the generated ``.qmd``,
  which is not in the repository), "Report an issue", and "Open in molab".
  The links only resolve once the ``.py`` is on the ``main`` branch, so they
  go live when the change merges.
- **piston editor.** The tutorial's JS editor (``mo.ui.code_editor``) only
  earns its place in the live notebook: the islands runtime renders it twice
  (it re-renders the cell output without removing the static snapshot, a
  marimo islands bug that shows outside Quarto too). The cell is dropped from
  the page and the piston iframe reads the editor's initial value instead,
  which stays on the page. The cell remains in the source notebooks
  (``symeval_mo.py`` / ``docs/getting_started.py``).

Under Quarto this runs from ``docs/`` with ``QUARTO_PROJECT_DIR`` set; by hand
it targets ``docs/`` regardless of the working directory::

    uv run scripts/docs_prerender.py
"""

from __future__ import annotations

import json
import os
import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
DOCS = REPO_ROOT / "docs"
sys.path.insert(0, str(DOCS / "_extensions" / "marimo" / "python"))

from quarto_marimo.prerender import (
    convert,
    find_notebooks,
    output_path,
    write_if_changed,
)

GITHUB_SLUG = "bedrock-engineer/symeval"
GITHUB_BRANCH = "main"

# One code cell as marimo exports it, capturing its body.
CELL_RE = re.compile(
    r"^```\{marimo \.python[^}]*\}[ \t]*\n(?P<code>.*?)\n```[ \t]*$",
    re.DOTALL | re.MULTILINE,
)


def page_links(notebook: Path) -> str:
    """Front matter that lists ``notebook``'s links under the table of contents.

    Quarto's own links (``repo-actions``) are turned off for the page and listed
    as ``code-links`` instead, in the same order and look (``docs/theme.scss``
    hides the "Code Links" heading). The molab link's trailing ``/wasm`` opens
    the notebook in the browser-only WASM sandbox rather than a cloud-backed
    molab session.
    """
    path = notebook.resolve().relative_to(REPO_ROOT).as_posix()
    blob = f"{GITHUB_SLUG}/blob/{GITHUB_BRANCH}/{path}"
    links = [
        ("View source", "github", f"https://github.com/{blob}"),
        ("Report an issue", "empty", f"https://github.com/{GITHUB_SLUG}/issues/new"),
        ("Open in molab", "play-circle", f"https://molab.marimo.io/github/{blob}/wasm"),
    ]
    lines = ["repo-actions: false", "code-links:"]
    for text, icon, href in links:
        lines += [
            f"  - text: {text}",
            f"    icon: {icon}",
            f"    href: {json.dumps(href)}",
        ]
    return "\n".join(lines) + "\n"


def strip_js_editor(body: str) -> str:
    """Remove the piston JS-editor cell; the page uses its initial value directly."""

    def _drop(match: re.Match[str]) -> str:
        if "piston_js_editor = mo.ui.code_editor" in match.group("code"):
            return ""
        return match.group(0)

    body = CELL_RE.sub(_drop, body)
    return body.replace("piston_js_editor.value", "initial_piston_js_str")


def symeval_page(notebook: Path) -> str:
    """The Quarto page for ``notebook``, with the SymEval page tweaks."""
    page = convert(notebook, transform=lambda body, _: strip_js_editor(body))
    # The page opens with its front matter; the links go at its end.
    end = page.index("\n---\n", len("---\n")) + 1
    return page[:end] + page_links(notebook) + page[end:]


def main() -> None:
    project_dir = Path(os.environ.get("QUARTO_PROJECT_DIR", DOCS)).resolve()
    for notebook in find_notebooks(project_dir):
        page = output_path(notebook)
        if write_if_changed(page, symeval_page(notebook)):
            print(f"wrote {os.path.relpath(page)}")


if __name__ == "__main__":
    main()
