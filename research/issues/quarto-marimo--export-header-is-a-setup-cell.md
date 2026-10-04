# Issue draft → `marimo-team/quarto-marimo` (cross-reference `marimo-team/marimo`)

**Title:** `marimo export md --flavor qmd` writes the PEP 723 block under
`header:`, which the engine runs as a setup cell instead of reading as
`pyproject:`

---

## Summary

Export a notebook with `marimo export md --flavor qmd` and render the result
with quarto-marimo: every island renders, but the notebook's dependencies are
missing. The exporter writes the inline script metadata under `header:`. The
engine reads dependencies from `pyproject:` and treats `header:` as a Python
setup cell that runs before the authored cells (`document.py`). A block of
comments is a no-op setup cell, so the `uv` sandbox is built without the
notebook's packages, and every cell that imports one shows
`ModuleNotFoundError` inside its island. `quarto render` exits 0, because the
`error` cell option defaults to `true`.

Renaming the key is the complete fix. `engine: marimo` is not needed: the
engine claims a page by its cell fences (`claimsFile` in `src/engine/index.ts`).

## Environment

- marimo `0.25.1` (exporter)
- quarto-marimo `0.5.0`, installed with `quarto add marimo-team/quarto-marimo`
- Quarto `1.10.18`, Linux

## Reproduction

`nb.py`, a notebook with a PEP 723 header declaring `sympy`, a `mo.md` cell, a
cell that expands `(x + 1) ** 3` with SymPy, and a `hide_code` markdown cell:

```sh
uvx marimo@0.25.1 export md --flavor qmd nb.py -o raw.qmd
quarto render raw.qmd --to html
```

The export's frontmatter:

```yaml
title: Nb
marimo-version: 0.25.1
width: medium
header: |-
  # /// script
  # requires-python = ">=3.12"
  # dependencies = [
  #     "marimo",
  #     "sympy",
  # ]
  # ///
```

**Actual:** exit 0, two `<marimo-quarto-island>` elements. The island payload
reports `runtimeCellCount: 3` (the header became a third, setup, cell) and the
SymPy cell's output is
`{"type": "exception", "msg": "No module named 'sympy'", "exception_type": "ModuleNotFoundError"}`.

**With `header: |-` replaced by `pyproject: |` and nothing else changed:** exit
0, two islands, `runtimeCellCount: 2`, `uv` installs 27 packages, and the cell
shows `x^3 + 3x^2 + 3x + 1`. Adding or omitting `engine: marimo` makes no
difference in either case (four variants rendered).

## Suggested fix

Either side could move:

- quarto-marimo: `command.py` already accepts a block whose first line is
  `# /// script` verbatim. Reading `header:` as `pyproject:` when it starts
  that way is a few lines in `document.py` and keeps `header:` working as a
  setup cell for everything else.
- marimo: have the `qmd` flavor write `pyproject:`, the key this engine
  documents.

Separately, a cell that raises at build time exits 0 by default. Quarto's own
engines fail the render unless `error: true` is set; per-cell `#| error: false`
does fail the render here (`RuntimeError: marimo execution failed`). A
page-level default of `false` would have made this report a build failure
instead of a page with an error box.

(A pre-render step that does the rename, titles the page after its opening
heading and shows the notebook's code is in
[bedrock-engineer/quarto-marimo](https://github.com/bedrock-engineer/quarto-marimo),
branch `feat/prerender-notebooks`; happy to open it as a PR.)
