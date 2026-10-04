# /// script
# requires-python = ">=3.12"
# dependencies = [
#     "marimo",
# ]
# ///
"""Convert the marimo notebooks in a Quarto project into ``.qmd`` pages.

Every marimo notebook ``<name>.py`` below the project directory becomes a
``<name-kebab>.qmd`` next to it, so where a notebook lives decides the page's
URL (snake_case is the Python convention, kebab-case the web one)::

    docs/getting_started.py      ->  docs/getting-started.qmd  ->  /getting-started.html
    docs/examples/cantilever.py  ->  docs/examples/cantilever.qmd

Directories Quarto itself ignores (names starting with ``_`` or ``.``, such as
``_site``, ``_extensions`` and ``__marimo__``) are skipped, as are ``.py``
files that are not marimo notebooks.

Each notebook is exported with ``marimo export md --flavor qmd``. That output is
not something the quarto-marimo engine (>= 0.5) consumes as-is, so two fixes
are applied, plus a build-time code display:

1. **Frontmatter.** marimo writes the PEP 723 script metadata under a
   ``header:`` key; the extension only reads ``pyproject:`` (verified: a
   dependency declared under ``header:`` is not installed in the render
   sandbox). ``marimo-version`` is dropped, and ``engine: marimo`` is added
   because quarto-marimo >= 0.5 no longer claims files by scanning for fences.
   The rest of marimo's frontmatter (``title``) passes through unchanged.

2. **Code display.** An island hides its code by default, and while 0.5.0's
   ``#| echo: true`` shows a read-only code block, it renders client-side after
   hydration, gets no Quarto syntax highlighting or copy button, and hidden
   cells would lose their code entirely (``#| code-fold`` is a no-op on
   islands). So the code is rendered at build time:

   - **visible cell** -> a ```` ```python ```` block *above* the island (code,
     then the island's output);
   - **hidden cell** (``hide_code="true"``) -> a collapsible ``<details>`` with
     the code, then the island (output only).

   The island keeps marimo's native ```` ```{marimo .python} ```` fence
   unchanged; quarto-marimo 0.5.0 consumes it directly.

Nothing in this file is specific to one project. Project-specific page tweaks
go through the ``transform`` hook of :func:`convert_all` (a callable that gets
each page's body and returns the body to use), from a small wrapper script that
serves as the project's ``pre-render:`` hook.

The ``.py`` notebooks are the source of truth; the ``.qmd`` files are build
artifacts. A ``.qmd`` is only rewritten when its content changed, which keeps
``quarto preview`` stable when this runs as the ``pre-render:`` hook (Quarto
runs hooks from the project directory and sets ``QUARTO_PROJECT_DIR``)::

    uv run scripts/mo_to_qmd.py [PROJECT_DIR]
"""

from __future__ import annotations

import os
import re
import subprocess
import sys
import tempfile
from collections.abc import Callable
from pathlib import Path

# A page hook: ``transform(body, notebook) -> body``. ``body`` is the exported
# page below its frontmatter, with marimo's ```{marimo .python}``` cell fences
# intact (the code display is added afterwards); ``notebook`` is the source .py.
Transform = Callable[[str, Path], str]

# One marimo-exported code cell: ```{marimo .python}``` or the hidden-code
# variant ```{marimo .python hide_code="true"}```, capturing the cell body.
CELL_RE = re.compile(
    r'^```\{marimo \.python(?P<hide> hide_code="true")?\}[ \t]*\n'
    r"(?P<code>.*?)\n"
    r"```[ \t]*$",
    re.DOTALL | re.MULTILINE,
)


def is_marimo_notebook(path: Path) -> bool:
    """Whether ``path`` is a marimo notebook (defines ``app = marimo.App(...)``)."""
    text = path.read_text(encoding="utf-8")
    return re.search(r"^\w+ = marimo\.App\(", text, re.MULTILINE) is not None


def find_notebooks(project_dir: Path) -> list[Path]:
    """The marimo notebooks under ``project_dir``, skipping ``_``/``.`` directories."""
    return sorted(
        path
        for path in project_dir.rglob("*.py")
        if not any(part[0] in "_." for part in path.relative_to(project_dir).parts)
        and is_marimo_notebook(path)
    )


def output_path(notebook: Path) -> Path:
    """The ``.qmd`` written for ``notebook``: same directory, kebab-case stem."""
    return notebook.with_name(f"{notebook.stem.replace('_', '-')}.qmd")


def export_qmd(notebook: Path) -> str:
    """marimo's own qmd-flavoured markdown export of ``notebook``."""
    with tempfile.TemporaryDirectory() as tmp:
        out = Path(tmp) / "export.qmd"
        subprocess.run(
            [sys.executable, "-m", "marimo", "export", "md", "--flavor", "qmd",
             str(notebook), "-o", str(out), "-f"],
            check=True,
        )
        return out.read_text(encoding="utf-8")


def split_frontmatter(text: str) -> tuple[list[str], str]:
    """Split a ``---`` delimited YAML frontmatter from the document body."""
    if not text.startswith("---\n"):
        return [], text
    end = text.index("\n---\n", 4)
    return text[4:end].splitlines(), text[end + 5 :]


def fix_frontmatter(front: list[str]) -> list[str]:
    """Make marimo's frontmatter consumable by quarto-marimo >= 0.5.

    ``header: |-`` becomes ``pyproject: |`` (its indented block passes through),
    ``marimo-version`` is dropped, and ``engine: marimo`` is added; without it
    the ``{marimo .python}`` cells render as literal text.
    """
    fixed = ["engine: marimo"]
    for line in front:
        if line.startswith("marimo-version:"):
            continue
        if re.match(r"header:\s*\|", line):
            line = "pyproject: |"
        fixed.append(line)
    return fixed


def _render_cell(match: re.Match[str]) -> str:
    """Add the build-time code display to one marimo-exported cell (island)."""
    code = match.group("code")
    island = match.group(0)
    display = f"```python\n{code}\n```"
    if match.group("hide") is not None:
        return (
            "<details>\n<summary>Show code</summary>\n\n"
            f"{display}\n\n"
            "</details>\n\n"
            f"{island}"
        )
    return f"{display}\n\n{island}"


def add_code_display(body: str) -> str:
    """Put a read-only code block (collapsible for hidden cells) above every island."""
    return CELL_RE.sub(_render_cell, body)


def convert(notebook: Path, transform: Transform | None = None) -> str:
    """The finished ``.qmd`` page for ``notebook``."""
    front, body = split_frontmatter(export_qmd(notebook))
    if transform is not None:
        body = transform(body, notebook)
    body = add_code_display(body).strip("\n")
    return "---\n" + "\n".join(fix_frontmatter(front)) + "\n---\n\n" + body + "\n"


def write_if_changed(path: Path, text: str) -> bool:
    """Write ``text`` to ``path`` unless it already holds it; return whether it wrote."""
    if path.exists() and path.read_text(encoding="utf-8") == text:
        return False
    path.write_text(text, encoding="utf-8")
    return True


def convert_all(project_dir: Path, transform: Transform | None = None) -> list[Path]:
    """Convert every notebook under ``project_dir``; return the ``.qmd`` paths."""
    notebooks = find_notebooks(project_dir)
    if not notebooks:
        raise SystemExit(f"No marimo notebooks found under {project_dir}")
    pages = []
    for notebook in notebooks:
        out = output_path(notebook)
        verb = "Wrote" if write_if_changed(out, convert(notebook, transform)) else "Unchanged"
        print(f"{verb} {os.path.relpath(out)}")
        pages.append(out)
    return pages


def main(argv: list[str] | None = None) -> None:
    args = sys.argv[1:] if argv is None else argv
    project_dir = Path(args[0]) if args else Path(os.environ.get("QUARTO_PROJECT_DIR", "."))
    convert_all(project_dir.resolve())


if __name__ == "__main__":
    main()
