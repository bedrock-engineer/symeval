# SymEval — TODO

## Package
- Shouldn't `subs` be an arg, rather than a kwarg? `subs` is not an optional input, right? What happens when subs = None, which is the default value right now?
    - Related inconsistency: `quantity_evalf` already accepts `subs` positionally, while `sym_evalf` forces keyword-only (bare `*`). Whatever the decision, make both agree. Deviating from `evalf`'s parameter order (`n` first) is fine, since `subs` is the essential input here. Note: `reference.qmd` currently shows a `*` in the `quantity_evalf` signature that isn't in the code; fix it along with this decision.
- Scalars in `subs` crash (`AttributeError: 'int' object has no attribute 'dimensionality'`), while sympy's `evalf` accepts plain numbers in its `subs`. Decide: coerce scalars to dimensionless quantities (more evalf-like), or keep requiring `Quantity(x, "")` and raise a clear `TypeError`. The docstrings say a dimensionless input must still be a `Quantity`, but `reference.qmd` claims scalars work (in both the `sym_evalf` and `quantity_evalf` parameter tables); align the docs with the decision.
- Align the SymEval API on `evalf()`'s API with `n=` (significant digits), and document that very clearly: `n` is numeric precision forwarded to `evalf`, `decimals` is presentation only (decimal places in the rendering) and never changes the computed quantity.
    - It doesn't make sense when `decimals` exceeds the decimal places that `n` actually resolves: the extra displayed digits are numerically meaningless. Note the comparison is not simply `n < decimals` (significant digits vs decimal places): the resolved decimal places are roughly `n - floor(log10(|result|)) - 1`, so it depends on the result's magnitude, and `output_unit` shifts it (the same `n` supports 6 more decimal places in MPa than in Pa).
    - Likely better: reframe `decimals` as `n_display` (significant figures for the rendering), formatted like [sciform](https://sciform.readthedocs.io)'s sig_fig engineering formatter. This dissolves the caveat above: `n` and `n_display` are then both significant figures, so the sanity check is a direct `n >= n_display`. Sig figs are also magnitude-proof (unaffected by `output_unit`) and match how engineers report results.
        - No sciform runtime dependency (keep the package minimal): sig-fig rounding + engineering notation is a small pure function inside our own rendering pipeline (`_format_quantity`). Don't use [pint's custom formats](https://pint.readthedocs.io/en/stable/user/formatting.html#custom-formats): `register_unit_format` hooks units only, and magnitude formatting would mean replacing the formatter on the user's registry, which is invasive and against the no-bundled-registry stance.
        - Do consider sciform as a dev-only test oracle: property-test our formatter against `sciform.Formatter(round_mode="sig_fig", ...)`.
        - Open: replace `decimals` outright (preferred, pre-1.0) or keep both knobs? Default `n_display=4`? Engineering-notation exponent mainly matters for the SI-base fallback and the verbose line, since a prefixed `output_unit` already does the scaling.
        - Substituted inputs: keep the current philosophy, translated to sig figs. Today they render at `decimals+1` places with trailing zeros trimmed, so inputs are rounded (deliberately, to hide pint's float conversion noise) but never padded. The sig-figs analogue is `n_display+1` sig figs, trailing zeros trimmed.
- `output_symbol` is only needed when passing an `sympy.Expr`, rather than a `sympy.Equality`. Right now I think the `output_symbol` is making the API a little more complicated. What would you suggest? Put the `output_symbol` last?
- Why is speed shown in m/h, rather than m/s in the pre-answer?
- Build something that works well for functions, such as e.g.
    `f(x)=1.9sin((2π/2.36)x)`


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
