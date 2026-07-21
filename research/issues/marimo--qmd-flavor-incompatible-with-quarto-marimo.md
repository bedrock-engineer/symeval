# Issue draft → `marimo-team/marimo`

**Title:** `marimo export md --flavor qmd` output is not rendered by the current `quarto-marimo` extension (frontmatter key + code-fence form mismatch)

---

## Summary

`marimo export md --flavor qmd` produces a `.qmd` that the current
[`quarto-marimo`](https://github.com/marimo-team/quarto-marimo) engine extension
(0.4.5) does **not** render as interactive islands. Two things are emitted in a
form the extension no longer consumes:

1. **Frontmatter key.** The exporter writes `header:`; the extension reads
   `pyproject:` (see `command.py` / `extract.py` in quarto-marimo, which lift
   `pyproject` into the PEP 723 script metadata).
2. **Code fence.** The exporter writes ```` ```{marimo .python} ```` (Quarto engine
   `marimo`, class `.python`); the extension auto-detects
   ```` ```{python .marimo} ```` (engine `python`, class `.marimo`). The language
   token and the class are effectively **swapped**.

Net effect: the exported notebook renders with **zero** marimo islands — the
cells fall through to Quarto's Jupyter engine and are not hydrated.

## Environment

- marimo `0.23.14`
- quarto-marimo extension `0.4.5`
- Quarto `1.9.38` (installed via the `quarto-cli` PyPI wheel)
- Linux (WSL2)

## Reproduction

```sh
uvx marimo export md --flavor qmd notebook.py -o out.qmd
```

`out.qmd` frontmatter and cells look like:

```yaml
---
title: ...
marimo-version: 0.23.14
header: |-
  # /// script
  # dependencies = ["marimo", ...]
  # ///
---
```

```` ```{marimo .python} ````

Then, in a Quarto project with the extension installed
(`quarto add marimo-team/quarto-marimo`):

```sh
quarto render out.qmd
```

**Actual:** no `marimo-island` elements in the output HTML; cells are not
interactive.

**Expected:** interactive marimo islands.

## Evidence

Rendering three minimal fence forms with the 0.4.5 extension (one trivial
`import marimo as mo; mo.md("hi")` cell each):

| Fence | Source | `marimo-island` markers |
| --- | --- | --- |
| ```` ```{marimo .python} ```` | `marimo export --flavor qmd` | **0** |
| ```` ```{python .marimo} ```` | quarto-marimo's documented form | 3 |
| ```` ```python {.marimo} ```` | (display block + `.marimo` attr) | 3 |

The extension's own `marimo-deprecated.lua` confirms the intended form:

> "The marimo engine extension now auto-detects `{python .marimo}` code blocks."

A side-by-side of the raw export vs. a hand-corrected version is attached
(`getting-started_export.qmd` vs `getting-started_corrected-export.qmd`): the
only differences are `header:` → `pyproject:` and `{marimo .python}` →
`{python .marimo}`.

## Suggested fix

Have the `qmd` flavor emit output the current `quarto-marimo` engine consumes:
`pyproject:` frontmatter and ```` ```{python .marimo} ```` fences. (Or coordinate a
single canonical format with the quarto-marimo maintainers — cross-reference to
a companion issue on that repo.)
