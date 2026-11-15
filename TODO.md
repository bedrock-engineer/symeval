# SymEval — TODO

## Package
- Consider [sciform](https://sciform.readthedocs.io) as a dev-only test oracle for the sig-fig engineering formatter: property-test `_format_quantity` against `sciform.Formatter(round_mode="sig_fig", ...)`. (The `n_display` reframe itself shipped: `decimals` replaced by `n_display` significant figures, `Decimal`-based formatter, `n >= n_display` warning, `subs` positional in both entry points, plain numbers coerced to dimensionless, `output_symbol` moved last.)
- Re-record the example clips (`media/recorders/`: piston, hss, table) and re-render the promo video (`media/remotion/`) **before** the `n_display` release: they show the old `decimals=` API and old number formatting. Serve locally against the current source (see "API-breaking releases" in `RELEASING.md`), record, commit, then release.
- Move the sandbox/reproducibility checks to CI: the release gate now runs in the locked project env (`pre_build`, `test`, `docs_session` all `uv run`), so nothing regularly verifies that `symeval_mo.py`'s and `docs/getting_started.py`'s PEP 723 headers still work for a fresh `uvx marimo edit --sandbox` user. A scheduled or per-PR CI job should run the sandbox session exports.
- Show expected vs actual rendering visually for all (or most) tests, so a rendering that is green but ugly still gets caught by eye. Group tests by theme, each theme in its own marimo column. Never in column 0: that holds the implementation plus the curated Getting started tutorial, which is extracted into `docs/getting_started.py`, the docs and the README.
- Build something that works well for functions, such as e.g.
    `f(x)=1.9sin((2π/2.36)x)`
- Switch the substituted-value spacing from `\medspace` to `\thinspace` in the library source (`symeval_mo.py`, `_render_substituted`: the `\medspace\left(...\right)` wrap and the `\medspace{formatted}` replace). `\medspace` is an amsmath macro GitHub's MathJax does not define (renders the literal name in red); `\thinspace` is plain TeX (defined without amsmath) and letters-only, so it survives GitHub Markdown's backslash-escaping (unlike `\,`, which unescapes to a literal comma) and renders on GitHub, PyPI's MathJax, and KaTeX (marimo/Jupyter). Do this live via marimo-pair and eyeball the slightly tighter 3mu vs 4mu gap. Once the source emits `\thinspace`, delete the `\medspace`→`\thinspace` replacement in `scripts/docs_to_readme.py` (`_tidy_latex`) so the spacing command has a single source of truth (the downstream replace is the current working stopgap).


## Examples

Longer, more complete demos, each a marimo notebook directly in `docs/` (no separate examples folder), rendered to a page next to it by the pre-render hook, with an "Open in molab" link:
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

## Upstream issues
**Next step: file these upstream** (drafts handed over 2026-11-15, outside the repo). Each one lets this repo or the quarto-marimo fork drop a workaround once it is fixed:

- marimo: islands render a `mo.ui.code_editor` output twice (also on a Starlight page, so not Quarto-specific). Workaround: `strip_js_editor` in `scripts/docs_prerender.py` drops the piston editor cell from the docs page; once fixed, consider putting the editor back.
- marimo: the islands runtime does not define `__resizeIframe`, which every `mo.iframe` output calls on load. Workaround: the quarto-marimo fork's browser header defines it.
- mdx-marimo: the islands-bridge stylesheet's `overflow-x: auto` forces `overflow-y: auto`, giving KaTeX and tree outputs a tiny vertical scrollbar. Workaround: the quarto-marimo fork's host stylesheet restores `overflow: visible`.
- quarto-marimo: the engine runs a raw `marimo export md --flavor qmd` file's `header:` (the PEP 723 block) as a setup cell, so the notebook's dependencies are never installed. Workaround: the fork's pre-render step renames it to `pyproject:`.

The generic notebook-to-page step lives in the quarto-marimo fork (`integration` branch, headed upstream), not in this repo; `scripts/docs_prerender.py` only adds the page links (GitHub and molab) and drops the piston editor cell. So do the widget fixes for Quarto's Bootstrap (marimo widgets inherit Bootstrap's grid and form styles inside their shadow roots), which made the table checkboxes and the radio look wrong.
