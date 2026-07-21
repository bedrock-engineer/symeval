# SymEval — TODO

## Package
- Shouldn't `subs` be an arg, rather than a kwarg? `subs` is not an optional input, right? What happens when subs = None, which is the default value right now?
- `output_symbol` is only needed when passing an `sympy.Expr`, rather than a `sympy.Equality`. Right now I think the `output_symbol` is making the API a little more complicated. What would you suggest? Put the `output_symbol` last?
- Why is speed shown in m/h, rather than m/s in the pre-answer?
- Build something that works well for functions, such as e.g.
    `f(x)=1.9sin((2π/2.36)x)`


## Examples

### In the `examples/` folder
Longer, more complete demos:
- The [Explorable Explanations](https://worrydream.com/ExplorableExplanations) example.
- Simply Supported Beam with Linearly Distributed Load: https://imartincei.github.io/CalcpadCE/examples/simply-supported-beams.html
- Cantilever with Partially Distributed Load: https://imartincei.github.io/CalcpadCE/examples/cantilevers.html
- Fully Restrained Beam with Uniformly Distributed Load: https://imartincei.github.io/CalcpadCE/examples/fully-restrained-beams.html
- Terzaghi bearing capacity calculation.

## Docs

### README.md
- Populate README with getting_started.py output.
    - Align the LaTeX from the Euler buckling stress working (the chained calculation).
    - The `\,` are thin-space separators that `sympy.latex` emits. MathJax renders them as spaces (VSCode preview, the docs site), but PyPI renders no math at all and shows the raw source, so the `$$...$$` blocks look like commas everywhere. Direction: render the working to images (PNG/SVG) for the README rather than raw LaTeX.
- piston widget .gif. Make the .gif with remotion?

Guide and inspiration:
- Good README guide: https://github.com/banesullivan/README + Inspiration section
- Awesome example: [marimo](https://github.com/marimo-team/marimo)'s README is awesome

### Website

Diataxis-style docs. Inspiration:
- https://quarto.org
- https://docs.marimo.io
- https://docs.pyvista.org/user-guide/data_model
- https://fastapi.tiangolo.com & https://sqlmodel.tiangolo.com & https://typer.tiangolo.com
- https://geopandas.org/en/stable (Flow: Getting Started → Installation → Introduction to GeoPandas: https://geopandas.org/en/stable/getting_started/introduction.html#Concepts)

#### Notes

- Expand the **examples gallery**: the notebooks under `## Examples` above become `examples/*.py`, auto-rendered into `docs/examples/`.
- **Per-cell static vs reactive** on the tutorial: the intro (axial stress) was meant to be static and the rest reactive; currently all cells are reactive islands. Needs a `#| reactive:` marker driven from the source notebook.
- Paired `.py` + molab badges for the worked examples (only the tutorial has one for now).

#### Feedback (site review)

- Feedback on the Getting started guide, its interactive elements and code.
    Here it seems there's actually some bugs in how `quarto-marimo` and `marimo export md --flavor qmd` work.  
    I want to submit issues to the marimo and quarto-marimo repos to report these bugs, and then get stuff to work now by changing the scripts and modifying quarto-marimo. Then I might also want to submit PRs to quarto-marimo and/or marimo to resolve the issues we submitted.
    - Where did it come from that the
        ```{python .marimo}
        # marimo Python code
        ```
        syntax is deprecated? (which it says in the script) I'd say it's not. Quarto's [Code Blocks docs](https://quarto.org/docs/computations/python.html#code-blocks) specifically state that "Code blocks that use braces around the language name (e.g. ```{python}) are executable, and will be run by Quarto during render."
        `marimo export md --flavor qmd` exports a `header` instead of `pyproject`, and ```{marimo .python}``` instead of ```{python .marimo}```, see @./examples/getting-started_export.qmd vs @./examples/getting-started_corrected-export.qmd
        I'd say this is a `marimo export md --flavor qmd` bug?
    - `#| echo / editor / code-fold: true / false` special quarto comments
        - Not possible to only show code. When you use `#| echo: true` it directly shows the code **and** the editor. To me it makes more sense to show the code **or*** the editor, but not both at the same time.
        - The [quarto-marimo home page](https://marimo-team.github.io/quarto-marimo/index.html) states there's an `#| editor: true` special comment, but it actually doesn't do anything, and neither does #| echo: false, because that's default behavior anyway.
        - Not possible to make code collapsible. The `#| code-fold: true` flag doesn't do anything.
