# /// script
# requires-python = ">=3.12"
# ///
"""Fail the docs build when a marimo page rendered with zero islands.

The failure this guards against is silent: when quarto-marimo does not claim a
page (say the generated frontmatter lost ``engine: marimo``, or an upstream
format change broke fence detection), ``quarto render`` still exits 0 and
writes a page whose cells are literal text or simply absent. Nothing warns.
This ran as a manual Playwright probe until 2026-09-03; now it gates every
render as a Quarto ``post-render:`` script (see ``docs/_quarto.yml``).

The check is deliberately outside the extension: an extension-side warning can
only fire once the engine has claimed the document, which is exactly the step
that fails silently.

For every rendered page whose source ``.qmd`` contains a marimo cell fence,
require at least one ``<marimo-quarto-island>`` in the output HTML.

Runs from the Quarto project directory (``docs/``) with the environment Quarto
provides; falls back to scanning the project tree when invoked by hand.
"""

from __future__ import annotations

import os
import re
import sys
from pathlib import Path

# marimo's native fence and the extension's alternate form, either bare or with
# attributes (e.g. hide_code="true").
FENCE_RE = re.compile(r"^```\{(?:marimo \.python|python \.marimo)[^}]*\}", re.MULTILINE)


def main() -> None:
    project_dir = Path(os.environ.get("QUARTO_PROJECT_DIR", ".")).resolve()
    output_dir = Path(
        os.environ.get("QUARTO_PROJECT_OUTPUT_DIR", project_dir / "_site")
    )
    if not output_dir.is_absolute():
        output_dir = project_dir / output_dir

    failures: list[str] = []
    checked = 0
    for qmd in sorted(project_dir.rglob("*.qmd")):
        rel = qmd.relative_to(project_dir)
        if rel.parts[0] in ("_site", "_extensions"):
            continue
        if not FENCE_RE.search(qmd.read_text()):
            continue
        html = output_dir / rel.with_suffix(".html")
        checked += 1
        if not html.exists():
            failures.append(f"{rel}: no rendered output at {html}")
        elif "marimo-quarto-island" not in html.read_text():
            failures.append(f"{rel}: rendered with zero marimo islands")

    if failures:
        for f in failures:
            print(f"ERROR (check_islands): {f}", file=sys.stderr)
        sys.exit(1)
    print(f"check_islands: {checked} marimo page(s) OK")


if __name__ == "__main__":
    main()
