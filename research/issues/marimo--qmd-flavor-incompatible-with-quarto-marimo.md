# Issue draft → `marimo-team/marimo`

**Title:** `marimo export md --flavor qmd` output does not render under
quarto-marimo: `header:` vs `pyproject:` frontmatter, and no `engine: marimo`
line

---

## Summary

`marimo export md --flavor qmd` produces a `.qmd` that the quarto-marimo
engine extension does not render as interactive islands, and `quarto render`
exits 0 with no warning: the page simply has zero islands and the frontmatter
dumped into the body as text.

As of quarto-marimo `0.5.0` the fence form is **no longer part of the
problem**: the exporter's native ```` ```{marimo .python} ```` fences render
fine (verified, including the `hide_code="true"` attribute form). Two
mismatches remain:

1. **Frontmatter key.** The exporter writes the PEP 723 block under
   `header:`; the extension only reads `pyproject:`
   (`python/quarto_marimo/document.py`). Verified: a dependency declared under
   `header:` is not installed in the render sandbox and its import fails in
   the rendered output, while the same block under `pyproject:` works.
2. **No `engine: marimo`.** quarto-marimo `0.5.0` removed the
   `marimo-deprecated.lua` filter that claimed files by scanning for fences,
   so a page is only routed to the marimo engine when its frontmatter says
   `engine: marimo`. The exporter does not emit that line, so the raw export
   renders as literal text.

## Environment

- marimo `0.24.0`
- quarto-marimo extension `0.5.0` (on `0.4.5` the fence form was a third
  mismatch; fixed since)
- Quarto `1.10.18` (installed via the `quarto-cli` PyPI wheel)
- Linux (WSL2)

## Reproduction

```sh
uvx marimo export md --flavor qmd notebook.py -o out.qmd
quarto render out.qmd   # extension installed via quarto add marimo-team/quarto-marimo
```

**Actual:** exit 0; no islands; `header:` block visible as body text.

**Expected:** interactive marimo islands, or at minimum a warning that the
page was not claimed by the marimo engine.

Renaming `header:` to `pyproject:` and adding `engine: marimo` to the
frontmatter is the complete fix on `0.5.0`: with only those two edits the
export renders with all islands (verified on a 16-cell notebook).

## Suggested fix

Have the `qmd` flavor emit `pyproject:` instead of `header:` and include
`engine: marimo` in the frontmatter. Failing that, the silence is the worst
part: a document routed past the marimo engine renders cell fences as literal
text with exit 0, so a warning from either side would already help.
(Cross-reference to a companion issue on the quarto-marimo repo if the
maintainers prefer the extension to accept `header:`.)
