# /// script
# requires-python = ">=3.12"
# dependencies = [
#     "marimo",
# ]
# ///
"""The docs site's Quarto ``pre-render:`` hook: notebooks to pages, SymEval style.

``mo_to_qmd.py`` does the generic work (every marimo notebook under ``docs/``
becomes a ``.qmd`` next to it). This script runs it with the page tweaks that
are specific to this repository, applied to each page's body before the code
display is added:

- **molab badge.** An "Open in molab" link to the notebook on GitHub at both
  the top and the bottom of the page, so a reader can jump to the live notebook
  from either end. The badge only resolves once the ``.py`` is on the ``main``
  branch, so it goes live when the change merges.
- **piston editor.** The tutorial's JS editor (``mo.ui.code_editor``) only
  earns its place in the live notebook: the islands runtime renders it twice
  (it re-renders the cell output without removing the static snapshot; see
  ``research/issues/marimo--islands-duplicate-code-editor.md``). The cell is
  dropped from the page and the piston iframe reads the editor's initial value
  instead, which stays on the page. The cell remains in the source notebooks
  (``symeval_mo.py`` / ``docs/getting_started.py``).

Under Quarto this runs from ``docs/`` with ``QUARTO_PROJECT_DIR`` set; by hand
it targets ``docs/`` regardless of the working directory::

    uv run scripts/docs_prerender.py
"""

from __future__ import annotations

import os
from pathlib import Path

from mo_to_qmd import CELL_RE, convert_all

REPO_ROOT = Path(__file__).resolve().parent.parent
DOCS = REPO_ROOT / "docs"

GITHUB_SLUG = "bedrock-engineer/symeval"
GITHUB_BRANCH = "main"
BADGE_IMG = "https://marimo.io/molab-shield.svg"


def molab_badge(notebook: Path) -> str:
    """The HTML badge that opens ``notebook`` (as hosted on GitHub) in molab.

    The trailing ``/wasm`` opens the notebook in the browser-only WASM sandbox
    rather than a cloud-backed molab session. An HTML element rather than the
    ``![]()`` markdown form, so it renders identically at the top and bottom.
    """
    path = notebook.resolve().relative_to(REPO_ROOT).as_posix()
    url = f"https://molab.marimo.io/github/{GITHUB_SLUG}/blob/{GITHUB_BRANCH}/{path}/wasm"
    return f'<a href="{url}"><img src="{BADGE_IMG}" alt="Open in molab"></a>'


def strip_js_editor(body: str) -> str:
    """Remove the piston JS-editor cell; the page uses its initial value directly."""

    def _drop(match) -> str:
        if "piston_js_editor = mo.ui.code_editor" in match.group("code"):
            return ""
        return match.group(0)

    body = CELL_RE.sub(_drop, body)
    return body.replace("piston_js_editor.value", "initial_piston_js_str")


def symeval_page(body: str, notebook: Path) -> str:
    """The SymEval page tweaks, in ``mo_to_qmd``'s ``transform`` shape."""
    badge = molab_badge(notebook)
    body = strip_js_editor(body).strip("\n")
    return f"{badge}\n\n{body}\n\n{badge}"


def main() -> None:
    project_dir = Path(os.environ.get("QUARTO_PROJECT_DIR", DOCS)).resolve()
    convert_all(project_dir, transform=symeval_page)


if __name__ == "__main__":
    main()
