# symeval — TODO

## Package

- Redesign package API such that the default is to work with SymPy equations, rather than Expressions.
- Build something that works well for functions, such as e.g.
    `f(x)=1.9sin((2π/2.36)x)`


### Maybe?
- Possibly it would be nice to make symeval work properly with significant figures. [SciForm](https://sciform.readthedocs.io/en/stable) might be a good tool for that. Also the engineering formatter with `exp_mode="engineering"` in a custom Pint formatter (see last paragraph of https://pint.readthedocs.io/en/stable/user/formatting.html) seems nice.

## Examples

### mo.ui.batch for handcalcs example

- https://docs.marimo.io/api/inputs/batch

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
- The 📊 **DataFrame-ready** highlight is still a little verbose
- Is it possible to create a taskipy task to export the code and output of certain (named) cells from `symeval_mo.py`?

### Website
I want to create a docs website. I'm not sure yet what type. I like the [Diataxis](https://diataxis.fr/) approach, which is largely adopted by some of the projects that are an example to me when it comes to docs:
- https://quarto.org
- https://docs.marimo.io
- https://docs.pyvista.org/user-guide/data_model
- https://fastapi.tiangolo.com & https://sqlmodel.tiangolo.com & https://typer.tiangolo.com
- https://geopandas.org/en/stable, although it's not intuitive enough to me how to get to the core concept explanation:
    Flow: Getting Started → Installation → Introduction to GeoPandas: https://geopandas.org/en/stable/getting_started/introduction.html#Concepts

Wish list:
- Build it using either [Quarto](https://quarto.org) or [Zensical](https://zensical.org). Let's implement both, such that I can choose which I like better later.
- Have all the notebooks in `examples/` in the docs, but also have tests in the example notebooks, while keeping those tests out of the docs.
