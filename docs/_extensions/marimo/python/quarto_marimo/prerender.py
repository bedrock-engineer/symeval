"""Export the marimo notebooks in a Quarto project to Quarto Markdown.

`marimo export md --flavor qmd` writes a page this engine renders, with a few
things left over. The inline script metadata lands under `header:`, which the
engine runs as a setup cell rather than reading for dependencies, and the
exporter records its own `marimo-version:`. The exporter also titles the page
after the file name, so a notebook that opens with a heading gets two titles.
And a notebook shows its code in the editor, hiding only the cells the author
collapsed, while a page shows no code unless asked.

This module settles all of that and writes the page next to the notebook, so a
Quarto `pre-render` step keeps `.qmd` pages in sync with the notebooks they come
from. The engine claims the page by its cell fences; no `engine:` line is
needed.
"""

from __future__ import annotations

import json
import os
import re
import subprocess
import sys
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Callable, Iterable

    Transform = Callable[[str, Path], str]

NOTEBOOK_APP_REGEX = re.compile(r"^\w+\s*=\s*marimo\.App\(", re.MULTILINE)
FRONTMATTER_REGEX = re.compile(r"\A---\n(?P<front>.*?\n)---\n(?P<body>.*)\Z", re.DOTALL)
HEADING_REGEX = re.compile(r"# (?P<title>\S[^\n]*)")
FENCE_REGEX = re.compile(r"(`{3,}|~{3,})")
DROPPED_KEYS = ("marimo-version",)

# A notebook shows its code in the editor and folds what the author hid, so the
# page does the same; `hide_code` cells fold through the engine's cell options.
# A cell error on a notebook page is a broken page, so it fails the render, as
# Quarto's own engines do.
PAGE_OPTIONS = ("echo: true", "error: false")


def find_notebooks(project_dir: Path) -> list[Path]:
    """Return the marimo notebooks Quarto would include, in a stable order.

    Quarto ignores paths whose name starts with `_` or `.`, which is also what
    keeps `_site`, `_extensions` and `__marimo__` out of the results.
    """
    notebooks = []
    for path in sorted(project_dir.rglob("*.py")):
        relative = path.relative_to(project_dir)
        if any(part.startswith(("_", ".")) for part in relative.parts):
            continue
        if is_notebook(path):
            notebooks.append(path)
    return notebooks


def is_notebook(path: Path) -> bool:
    """Report whether a Python file defines a marimo app."""
    try:
        source = path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return False
    return NOTEBOOK_APP_REGEX.search(source) is not None


def output_path(notebook: Path) -> Path:
    """Return the `.qmd` path for a notebook.

    The page lives beside the notebook, so the notebook's location in the
    project decides the page's URL. Underscores become dashes because the stem
    becomes part of that URL.
    """
    return notebook.with_name(f"{notebook.stem.replace('_', '-')}.qmd")


def export_markdown(notebook: Path) -> str:
    """Export one notebook with marimo's Quarto flavor."""
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "marimo",
            "export",
            "md",
            "--flavor",
            "qmd",
            str(notebook),
        ],
        capture_output=True,
        text=True,
        encoding="utf-8",
        check=False,
    )
    if result.returncode != 0:
        message = result.stderr.strip() or f"marimo could not export {notebook}"
        raise RuntimeError(message)
    return result.stdout


def promote_title(body: str) -> tuple[str | None, str]:
    """Split the notebook's opening heading off the body as the page title.

    The exporter titles a page after its file name. When the notebook opens
    with a level-one heading, that heading is the title the author chose, and
    leaving it in the body would print it a second time under Quarto's. Code
    cells before it do not count as content: a notebook often starts with
    `import marimo as mo`.
    """
    lines = body.split("\n")
    fence: str | None = None
    for index, line in enumerate(lines):
        if fence is not None:
            if line.startswith(fence):
                fence = None
            continue
        if not line.strip():
            continue
        opening = FENCE_REGEX.match(line)
        if opening is not None:
            fence = opening.group(1)
            continue
        heading = HEADING_REGEX.fullmatch(line)
        if heading is None:
            break
        rest = lines[:index] + lines[index + 1 :]
        if index < len(rest) and not rest[index].strip():
            del rest[index]  # the blank line that separated the heading
        return heading.group("title").strip(), "\n".join(rest).lstrip("\n")
    return None, body.lstrip("\n")


def rewrite_frontmatter(front: str, title: str | None = None) -> str:
    """Point the exported frontmatter at the keys this engine reads.

    Only top-level keys are touched; block scalar bodies are indented and pass
    through untouched.
    """
    lines: list[str] = []
    for line in front.splitlines():
        key = line.split(":", 1)[0] if ":" in line else ""
        if key in DROPPED_KEYS:
            continue
        if key == "header":
            # The engine resolves dependencies from `pyproject`, and `|-` would
            # strip the trailing newline the script metadata block needs.
            lines.append("pyproject: |")
            continue
        if key == "title" and title is not None:
            lines.append(f"title: {json.dumps(title, ensure_ascii=False)}")
            continue
        lines.append(line)
    lines.extend(PAGE_OPTIONS)
    return "\n".join(lines) + "\n"


def convert(notebook: Path, transform: Transform | None = None) -> str:
    """Export one notebook and return the Quarto Markdown page."""
    exported = export_markdown(notebook)
    match = FRONTMATTER_REGEX.match(exported)
    if match is None:
        raise RuntimeError(f"marimo exported {notebook} without frontmatter")
    title, body = promote_title(match.group("body"))
    if transform is not None:
        body = transform(body, notebook)
    return f"---\n{rewrite_frontmatter(match.group('front'), title)}---\n\n{body}"


def write_if_changed(path: Path, content: str) -> bool:
    """Write a page only when it differs, and report whether it was written.

    `quarto preview` watches the files it renders, so rewriting an unchanged
    page would send it round the render loop again.
    """
    if path.exists() and path.read_text(encoding="utf-8") == content:
        return False
    path.write_text(content, encoding="utf-8")
    return True


def convert_all(
    project_dir: Path,
    transform: Transform | None = None,
    notebooks: Iterable[Path] | None = None,
) -> list[Path]:
    """Convert every notebook in a project and return the pages that changed."""
    found = list(notebooks) if notebooks is not None else find_notebooks(project_dir)
    written = []
    for notebook in found:
        target = output_path(notebook)
        if write_if_changed(target, convert(notebook, transform)):
            written.append(target)
    return written


def project_directory(argv: list[str]) -> Path:
    """Resolve the project directory Quarto is rendering."""
    if argv:
        return Path(argv[0])
    return Path(os.environ.get("QUARTO_PROJECT_DIR") or Path.cwd())


def main(argv: list[str] | None = None) -> int:
    """Run the pre-render conversion for one Quarto project."""
    project_dir = project_directory(list(sys.argv[1:] if argv is None else argv))
    for page in convert_all(project_dir):
        sys.stdout.write(f"quarto-marimo: wrote {page}\n")
    return 0
