# symeval — TODO

## Package

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
Guide and inspiration:
- Good README guide: https://github.com/banesullivan/README + Inspiration section
- Awesome example: [marimo](https://github.com/marimo-team/marimo)'s README is awesome

TODO:
- Is it possible to create a taskipy task to export the code and output of certain (named) cells from `symeval_mo.py`?

### Website
I want to create a docs website. I like the [Diataxis](https://diataxis.fr/) approach, which is largely adopted by some of the projects that are an example to me when it comes to docs:
- https://quarto.org
- https://docs.marimo.io
- https://docs.pyvista.org/user-guide/data_model
- https://fastapi.tiangolo.com & https://sqlmodel.tiangolo.com & https://typer.tiangolo.com
- https://geopandas.org/en/stable, although it's not intuitive enough to me how to get to the core concept explanation:
    Flow: Getting Started → Installation → Introduction to GeoPandas: https://geopandas.org/en/stable/getting_started/introduction.html#Concepts

I want to build a [quarto-marimo](https://github.com/marimo-team/quarto-marimo) docs website. The pages that are marimo notebooks need to be both a .qmd as well as a .py file though, because otherwise it's not possible to create [Open in molab](https://molab.marimo.io/github) badges. I think I want to create a folder with example notebooks (.py) and a separate docs folder with the rest of the documentation in .qmd files, where some of those also contain some Python or marimo cells.
