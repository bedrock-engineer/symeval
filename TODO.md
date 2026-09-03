# SymEval — TODO

## Package
- Consider [sciform](https://sciform.readthedocs.io) as a dev-only test oracle for the sig-fig engineering formatter: property-test `_format_quantity` against `sciform.Formatter(round_mode="sig_fig", ...)`. (The `n_display` reframe itself shipped: `decimals` replaced by `n_display` significant figures, `Decimal`-based formatter, `n >= n_display` warning, `subs` positional in both entry points, plain numbers coerced to dimensionless, `output_symbol` moved last.)
- Re-record the example clips (`media/recorders/`: piston, hss, table) and re-render the promo video (`media/remotion/`) **before** the `n_display` release: they show the old `decimals=` API and old number formatting. Serve locally against the current source (see "API-breaking releases" in `RELEASING.md`), record, commit, then release.
- Move the sandbox/reproducibility checks to CI: the release gate now runs in the locked project env (`pre_build`, `test`, `docs_session` all `uv run`), so nothing regularly verifies that `symeval_mo.py`'s and `getting_started.py`'s PEP 723 headers still work for a fresh `uvx marimo edit --sandbox` user. A scheduled or per-PR CI job should run the sandbox session exports.
- Show expected vs actual rendering visually for all (or most) tests, so a rendering that is green but ugly still gets caught by eye. Group tests by theme, each theme in its own marimo column. Never in column 0: that holds the implementation plus the curated Getting started tutorial, which is extracted into `examples/getting_started.py`, the docs and the README.
- Build something that works well for functions, such as e.g.
    `f(x)=1.9sin((2π/2.36)x)`
- Switch the substituted-value spacing from `\medspace` to `\thinspace` in the library source (`symeval_mo.py`, `_render_substituted`: the `\medspace\left(...\right)` wrap and the `\medspace{formatted}` replace). `\medspace` is an amsmath macro GitHub's MathJax does not define (renders the literal name in red); `\thinspace` is plain TeX (defined without amsmath) and letters-only, so it survives GitHub Markdown's backslash-escaping (unlike `\,`, which unescapes to a literal comma) and renders on GitHub, PyPI's MathJax, and KaTeX (marimo/Jupyter). Do this live via marimo-pair and eyeball the slightly tighter 3mu vs 4mu gap. Once the source emits `\thinspace`, delete the `\medspace`→`\thinspace` replacement in `scripts/docs_to_readme.py` (`_tidy_latex`) so the spacing command has a single source of truth (the downstream replace is the current working stopgap).


## Examples

### In the `examples/` folder
Longer, more complete demos. These become the **examples gallery**: `examples/*.py` notebooks, auto-rendered into `docs/examples/`, each with a paired `.py` + molab badge (only the tutorial has one for now):
- The [Explorable Explanations](https://worrydream.com/ExplorableExplanations) example.
- Simply Supported Beam with Linearly Distributed Load: https://imartincei.github.io/CalcpadCE/examples/simply-supported-beams.html
- Cantilever with Partially Distributed Load: https://imartincei.github.io/CalcpadCE/examples/cantilevers.html
- Fully Restrained Beam with Uniformly Distributed Load: https://imartincei.github.io/CalcpadCE/examples/fully-restrained-beams.html
- Terzaghi bearing capacity calculation.

## Docs

### README.md
README inspiration:
- Good README guide: https://github.com/banesullivan/README + Inspiration section
- Awesome example: [marimo](https://github.com/marimo-team/marimo)'s README is awesome

### Website
Diataxis-style docs. Inspiration:
- https://quarto.org
- https://docs.marimo.io
- https://docs.pyvista.org/user-guide/data_model
- https://fastapi.tiangolo.com & https://sqlmodel.tiangolo.com & https://typer.tiangolo.com
- https://geopandas.org/en/stable (Flow: Getting Started → Installation → Introduction to GeoPandas: https://geopandas.org/en/stable/getting_started/introduction.html#Concepts)

Feedback (which maybe are (quarto-)marimo bugs too?):
- The checkboxes in the "quantity_evalf() on a DataFrame"-table don't show well which row is selected, and the radio renders horizontally instead of vertically. Drafted as an upstream issue: `research/issues/mo-ui-elements-not-so-nice-in-quarto.md` (on 0.5.0 the checkbox gained a barely visible checkmark but lost the row and hover highlights; the radio is unchanged).

## (quarto-)marimo issues
**Next step: file the drafts in `research/issues/` upstream** (re-capture the screenshots first; the Discord CDN links in the mo.ui draft expire). Then maybe submit PRs to quarto-marimo and/or marimo to resolve them. The drafts:

- `marimo--iframe-strips-newlines.md` → marimo: `mo.iframe` srcdoc newline stripping in static/session export (why `strip_js_editor`'s regex workaround exists; still reproduces on 0.24.0).
- `marimo--islands-duplicate-code-editor.md` → marimo: islands render a `mo.ui.code_editor` output twice (why the piston editor cell is stripped from the docs export via `strip_js_editor` in `scripts/examples_to_qmd.py`; once fixed upstream, consider putting the editor back on the docs page).
- `marimo--islands-resize-iframe-undefined.md` → marimo: every `mo.iframe` island logs `ReferenceError: __resizeIframe is not defined` (harmless, pre-existing on 0.4.5).
- `marimo--qmd-flavor-incompatible-with-quarto-marimo.md` → marimo: `marimo export md --flavor qmd` emits `header:` instead of `pyproject:` and ```` ```{marimo .python} ```` instead of ```` ```{python .marimo} ````, so quarto-marimo renders zero islands from it (why `examples_to_qmd.py` rewrites the export; see @./examples/getting-started_export.qmd vs @./examples/getting-started_corrected-export.qmd). The old "fence is deprecated" question is resolved: v0.5.0's docs state both fence forms are supported.
- `quarto-marimo--cell-option-handling.md` → quarto-marimo: updated for 0.5.0 and verified empirically (test page: `quarto-marimo--cell-options-test.qmd`). `#| echo: true` (read-only code, no editor) and `#| editor: true` (single live editor) now work; `code-fold`/`code-summary` are silently dropped, and `hide_code` cells map to `echo: false` even though marimo's hide_code semantics are "collapsed but revealable", i.e. `code-fold: true` (our `<details>` wrapper stays until upstream supports that). Still no per-cell static-vs-reactive marker (`#| reactive: true / false` suggestion).
- `quarto-marimo--islands-bridge-overflow-scrollbars.md` → quarto-marimo: 0.5.0's islands-bridge `overflow-x: auto` forces `overflow-y: auto`, giving every KaTeX/tree output a tiny vertical scrollbar. Worked around in `docs/theme.scss` (`overflow: visible` on the island containers); drop that override once fixed upstream.
- `mo-ui-elements-not-so-nice-in-quarto.md` → marimo: `mo.ui.table` selection state and `mo.ui.radio` orientation render with lower fidelity on islands than in the app (see Docs feedback above).

Follow-up now that 0.5.0 handles cell options properly: `scripts/examples_to_qmd.py` may be able to drop its hand-rendered read-only ```` ```python ```` blocks in favor of `#| echo: true`.
