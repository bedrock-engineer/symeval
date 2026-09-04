# /// script
# requires-python = ">=3.12"
# dependencies = [
#     "marimo",
# ]
# ///
"""Extract the tutorial cells of ``symeval_mo.py`` into a standalone notebook.

``symeval_mo.py`` is laid out in marimo columns, with the library implementation
living in a ``with app.setup:`` block (it monkeypatches ``sym_evalf`` /
``quantity_evalf`` onto sympy, so it must run before any cell) followed by three
columns:

    column 0 — the worked examples, opening with the "# Getting started with
               SymEval" markdown cell (a setup-cell explanation precedes it)
    column 1 — the library implementation exports (the ``## EXPORT`` cells)
    column 2 — the tests

This script writes the tutorial as a self-contained, single-column marimo
notebook to:

    examples/getting_started.py

Two spans are dropped: the ``with app.setup:`` block (the inline implementation)
and the setup-cell explanation before the tutorial heading. The header is taken
from before the setup block, and extraction begins at the "# Getting started
with SymEval" cell — ``getting_started.py`` imports the implementation from the
installed ``symeval`` package instead of defining it inline.

Those imports (``sympy``, ``symeval``) sit commented-out in the source, since
there the names come from the setup block. Here we uncomment them (and repair
the cell's ``return`` tuple) so the notebook is self-contained and openable in
molab.

The source notebook is a multi-column marimo app (``App(width="columns")``); the
extracted notebook is a plain single-column notebook, so the ``width="columns"``
layout and the ``column=0`` cell marker are stripped.

The generated ``.py`` is the source for the docs website: ``examples_to_qmd.py``
renders it (and the other ``examples/*.py``) to Quarto ``.qmd`` pages.

Run it with uv so the inline dependency metadata above provisions marimo::

    uv run scripts/extract_getting_started.py
"""

from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
SOURCE = REPO_ROOT / "symeval_mo.py"
NOTEBOOK = REPO_ROOT / "examples" / "getting_started.py"

# The implementation column defines these inline, so the examples import them
# commented-out. In the standalone notebook they come from the package.
_COMMENTED_IMPORT = re.compile(
    r"^(?P<indent>[ \t]*)#[ \t]*"
    r"(?P<stmt>(?:import|from)[ \t]+(?:sympy|symeval)\b.*)$",
    re.MULTILINE,
)

_FOOTER = 'if __name__ == "__main__":\n    app.run()\n'


def _rewrite_docs_dependencies(header: str) -> str:
    """Fix the PEP 723 dependency list for the standalone notebook.

    The source notebook lists ``pytest`` (for its test column) and defines the
    library inline. The standalone notebook has no tests and imports the
    library, so it drops ``pytest`` and adds ``symeval``.
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


def _single_column(header: str) -> str:
    """Drop the multi-column layout from the ``marimo.App`` definition."""
    return re.sub(r"marimo\.App\(\s*width=\"columns\"\s*\)", "marimo.App()", header)


def _strip_column_marker(column_zero: str) -> str:
    """Remove the ``column=0`` marker from the first cell decorator.

    marimo tags only the first cell of each column with ``column=N``. In a
    single-column notebook that marker is meaningless, so ``@app.cell(column=0,
    hide_code=True)`` becomes ``@app.cell(hide_code=True)`` and a lone
    ``@app.cell(column=0)`` collapses back to ``@app.cell``.
    """
    column_zero = re.sub(r"(@app\.cell\()column=\d+,\s*", r"\1", column_zero)
    column_zero = re.sub(r"@app\.cell\(column=\d+\)", "@app.cell", column_zero)
    return column_zero


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


# The standalone tutorial begins at this markdown heading. Everything before it,
# the `with app.setup:` block (the inline implementation) and the note explaining
# it, is left out: getting_started.py imports the implementation from the
# `symeval` package instead.
TUTORIAL_HEADING = "# Getting started with SymEval"


def _tutorial_cell_start(source: str) -> "int | None":
    """Offset of the `@app.cell` that renders the tutorial's opening heading."""
    heading = source.find(TUTORIAL_HEADING)
    if heading == -1:
        return None
    cells = list(re.finditer(r"^@app\.(?:cell|function)\b", source[:heading], re.MULTILINE))
    return cells[-1].start() if cells else None


def extract_examples_column(source: str) -> str:
    """Return a standalone single-column notebook holding the tutorial cells.

    The header stops before the `with app.setup:` block, leaving the inline
    implementation behind; extraction starts at the tutorial's opening markdown
    cell, skipping the setup-cell explanation before it.
    """
    setup = re.search(r"^with app\.setup\b", source, re.MULTILINE)
    tutorial_start = _tutorial_cell_start(source)
    next_column = re.search(r"^@app\.cell\(column=1\b", source, re.MULTILINE)
    if setup is None or tutorial_start is None or next_column is None:
        raise SystemExit(
            "Could not locate the notebook structure in symeval_mo.py — expected a "
            "`with app.setup:` block, a "
            f"'{TUTORIAL_HEADING}' markdown cell, and a `@app.cell(column=1 ...)`."
        )

    header = _single_column(_rewrite_docs_dependencies(source[: setup.start()]))
    column_zero = _strip_column_marker(source[tutorial_start : next_column.start()])

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
    NOTEBOOK.write_text(
        extract_examples_column(SOURCE.read_text(encoding="utf-8")), encoding="utf-8"
    )
    print(f"Wrote {NOTEBOOK.relative_to(REPO_ROOT)}")

    # Validate the extracted notebook. `marimo check` is static: it parses the
    # file and checks the reactive graph (cycles, multiply-defined names,
    # unparsable cells) without executing any cell. That means it does not
    # import symeval, so it stays decoupled from whichever version of the
    # package is installed — a run/execute check would instead fail on every
    # API change until the matching release is published.
    subprocess.run([sys.executable, "-m", "marimo", "check", str(NOTEBOOK)], check=True)
    print(f"Checked {NOTEBOOK.relative_to(REPO_ROOT)}: valid marimo notebook")


if __name__ == "__main__":
    main()
