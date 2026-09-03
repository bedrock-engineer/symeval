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
- The checkboxes in the "quantity_evalf() on a DataFrame"-table don't show well which row is selected. Only the row is highlighted, but the checkbox of the selected row is not checked.
- The radio button element renders horizontally, instead of vertically as in the marimo notebook.

## (quarto-)marimo issues
Here it seems there's actually some bugs in how `quarto-marimo` and `marimo export md --flavor qmd` work.  
I want to submit issues to the marimo and quarto-marimo repos to report these bugs, and then get stuff to work now by changing the scripts and modifying quarto-marimo. Then I might also want to submit PRs to quarto-marimo and/or marimo to resolve the issues we submitted.

- Upgrade `docs/_extensions` to quarto-marimo v0.5.0 (released 2026-08-25, we're on 0.4.5) in its own PR. Findings from a first attempt (2026-09-03, reverted):
    - v0.5.0 drops the fence auto-detection (the `marimo-deprecated.lua` filter is gone); without `engine: marimo` in the page frontmatter the `{python .marimo}` cells render as literal text. Fix: emit `engine: marimo` from `build_page` in `scripts/examples_to_qmd.py`.
    - With that fix the page rendered and the piston worked (hydration is faster too: v0.5.0 compiles the document as one shared marimo app and reuses the worker), but the getting-started page came out really messy. Investigate before upgrading.
    - The `{python .marimo}` fence is **not** deprecated in v0.5.0: the docs state both `python {.marimo}` and `{python .marimo}` are supported (which resolves the question below).
    - The duplicate `mo.ui.code_editor` island bug (see `research/issues/marimo--islands-duplicate-code-editor.md`) reproduces on v0.5.0 as well.
- The piston JS editor cell is stripped from the docs export (`strip_js_editor` in `scripts/examples_to_qmd.py`) because of that duplicate-editor bug; once it's fixed upstream, consider putting the editor back on the docs page.
- Where did it come from that the
    ```{python .marimo}
    # marimo Python code
    ```
    syntax is deprecated? (which it says in the script) I'd say it's not. Quarto's [Code Blocks docs](https://quarto.org/docs/computations/python.html#code-blocks) specifically state that "Code blocks that use braces around the language name (e.g. ```{python}```) are executable, and will be run by Quarto during render."
    `marimo export md --flavor qmd` exports a `header` instead of `pyproject`, and ```{marimo .python}``` instead of ```{python .marimo}```, see @./examples/getting-started_export.qmd vs @./examples/getting-started_corrected-export.qmd
    I'd say this is a `marimo export md --flavor qmd` bug?
- `#| echo / editor / code-fold: true / false` special quarto comments
    - Not possible to only show code. When you use `#| echo: true` it directly shows the code **and** the editor. To me it makes more sense to show the code **or*** the editor, but not both at the same time.
    - The [quarto-marimo home page](https://marimo-team.github.io/quarto-marimo/index.html) states there's an `#| editor: true` special comment, but it actually doesn't do anything, and neither does #| echo: false, because that's default behavior anyway.
    - Not possible to make code collapsible. The `#| code-fold: true` flag doesn't do anything.
    - No **per-cell static vs reactive** marker: on the tutorial the intro (axial stress) was meant to be static and the rest reactive, but currently all cells are reactive islands. Needs something like a `#| reactive: true / false` special comment driven from the source notebook.

The piston mo.iframe was not appearing in the Getting started guide. This is actually an issue with how marimo exports to HTML, as I understand it.
