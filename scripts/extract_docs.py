# /// script
# requires-python = ">=3.12"
# dependencies = [
#     "marimo",
# ]
# ///
"""Extract the examples column of ``symeval_mo.py`` into the Quarto docs.

``symeval_mo.py`` is laid out in three marimo columns:

    column 0 — the worked examples (the first column, before "# Implementation")
    column 1 — the library implementation (the ``## EXPORT`` cells)
    column 2 — the tests

This script slices out column 0 and writes it, in two steps, to:

    docs/index.py   — a standalone, single-column marimo notebook
    docs/index.qmd  — the same notebook exported to Quarto markdown

The examples call ``sym_evalf`` / ``quantity_evalf`` and use ``sympy``; in the
source notebook those names come from the implementation column, so their
imports sit commented-out. Here we uncomment them (and repair the cell's
``return`` tuple) so the docs notebook pulls them from the installed
``symeval`` package instead, making it self-contained.

Run it with uv so the inline dependency metadata above provisions marimo::

    uv run scripts/extract_docs.py
"""

from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
SOURCE = REPO_ROOT / "symeval_mo.py"
NOTEBOOK = REPO_ROOT / "docs" / "index.py"
QMD = REPO_ROOT / "docs" / "index.qmd"

# The implementation column defines these inline, so the examples import them
# commented-out. In the standalone docs notebook they come from the package.
_COMMENTED_IMPORT = re.compile(
    r"^(?P<indent>[ \t]*)#[ \t]*"
    r"(?P<stmt>(?:import|from)[ \t]+(?:sympy|symeval)\b.*)$",
    re.MULTILINE,
)

_FOOTER = 'if __name__ == "__main__":\n    app.run()\n'


def _rewrite_docs_dependencies(header: str) -> str:
    """Fix the PEP 723 dependency list for the standalone docs notebook.

    The source notebook lists ``pytest`` (for its test column) and defines the
    library inline. The docs notebook has no tests and imports the library, so
    it drops ``pytest`` and adds ``symeval``.
    """
    block = re.search(
        r"(?P<open># dependencies = \[\n)(?P<body>(?:#.*\n)*?)(?P<close># \]\n)",
        header,
    )
    if block is None:
        return header
    names = set(re.findall(r'"([^"]+)"', block["body"]))
    names.discard("pytest")
    names.add("symeval")
    body = "".join(f'#     "{name}",\n' for name in sorted(names))
    return (
        f"{header[: block.start()]}{block['open']}{body}"
        f"{block['close']}{header[block.end() :]}"
    )


def _bound_names(import_stmt: str) -> list[str]:
    """Return the names an ``import`` / ``from ... import`` statement binds."""
    stmt = import_stmt.split("#", 1)[0].strip()
    if stmt.startswith("from "):
        _, _, imported = stmt.partition(" import ")
    else:
        imported = stmt[len("import ") :]
    names = []
    for part in imported.split(","):
        alias = part.strip().split(" as ")[-1].strip()
        # `import a.b` binds `a`; `from m import a` binds `a`.
        names.append(alias.split(".")[0])
    return [n for n in names if n]


def _repair_import_cell_return(text: str, activated: list[str]) -> str:
    """Add the newly-activated names to the import cell's ``return`` tuple.

    marimo serializes each cell's outputs in its ``return`` line. Uncommenting
    imports adds definitions, so that tuple must grow to match — otherwise the
    generated notebook only self-heals once opened in marimo.
    """
    anchor = text.index("import marimo as mo")
    ret = re.search(r"\n(?P<indent>[ \t]+)return (?P<names>[^\n]+)", text[anchor:])
    if ret is None:
        return text
    existing = [n.strip() for n in ret.group("names").strip("()").split(",") if n.strip()]
    merged = sorted(set(existing) | set(activated))
    replacement = f"\n{ret.group('indent')}return {', '.join(merged)}"
    return text[: anchor + ret.start()] + replacement + text[anchor + ret.end() :]


def extract_examples_column(source: str) -> str:
    """Return a standalone notebook holding only the first (examples) column."""
    first_cell = re.search(r"^@app\.(?:cell|function)\b", source, re.MULTILINE)
    next_column = re.search(r"^@app\.cell\(column=1\b", source, re.MULTILINE)
    if first_cell is None or next_column is None:
        raise SystemExit(
            "Could not locate the column boundaries in symeval_mo.py — expected "
            "a `@app.cell(column=1 ...)` cell marking the start of column 1."
        )

    header = _rewrite_docs_dependencies(source[: first_cell.start()])
    column_zero = source[first_cell.start() : next_column.start()]

    activated: list[str] = []
    def _uncomment(match: re.Match[str]) -> str:
        activated.extend(_bound_names(match.group("stmt")))
        return f"{match.group('indent')}{match.group('stmt')}"

    column_zero = _COMMENTED_IMPORT.sub(_uncomment, column_zero)
    if activated:
        column_zero = _repair_import_cell_return(column_zero, activated)

    return f"{header}{column_zero.rstrip()}\n\n\n{_FOOTER}"


def main() -> None:
    NOTEBOOK.parent.mkdir(parents=True, exist_ok=True)
    NOTEBOOK.write_text(extract_examples_column(SOURCE.read_text()))
    print(f"Wrote {NOTEBOOK.relative_to(REPO_ROOT)}")

    # Validate the extracted notebook. `marimo check` is static: it parses the
    # file and checks the reactive graph (cycles, multiply-defined names,
    # unparsable cells) without executing any cell. That means it does not
    # import symeval, so it stays decoupled from whichever version of the
    # package is installed — a run/execute check would instead fail on every
    # API change until the matching release is published.
    subprocess.run([sys.executable, "-m", "marimo", "check", str(NOTEBOOK)], check=True)
    print(f"Checked {NOTEBOOK.relative_to(REPO_ROOT)}: valid marimo notebook")

    subprocess.run(
        [sys.executable, "-m", "marimo", "export", "md", "--flavor", "qmd",
         str(NOTEBOOK), "-o", str(QMD), "-f"],
        check=True,
    )
    print(f"Wrote {QMD.relative_to(REPO_ROOT)}")


if __name__ == "__main__":
    main()
