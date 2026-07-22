# SymEval

<index.qmd up to "Head to the [Getting started](getting-started.qmd)">

# More advanced SymEval functionality

<getting-started.qmd with tweaks:>

<delete>
# Getting started with SymEval

SymEval allows you to define SymPy equations, then substitute Pint quantities (value + unit), and then shows symbolically (LaTeX) you how to arrive at the result.
</delete>

## Axial stress under a compressive force

Also include the marimo outputs here

## `quantity_evalf()` on a DataFrame

"""
<p align="center">
  <img src="docs/public/table.gif" alt="Selecting a member row in the table updates its axial-stress symbolic evaluation below." width="760">
</p>

Open the [Getting started tutorial](https://bedrock-engineer.github.io/symeval/getting-started.html) on the docs website, or <open in molab badge> for the live, interactive version.  
"""  
instead of the marimo output.

## Axial resistance of a steel HSS member

"""
<p align="center">
  <img src="docs/public/hss.gif" alt="Increasing the beam length recomputes the Euler buckling stress, lambda factor, axial resistance, and demand-capacity ratio, with DCR rising past 1.0" width="620">
</p>

Open the [Getting started tutorial](https://bedrock-engineer.github.io/symeval/getting-started.html) on the docs website, or <open in molab badge> for the live, interactive version.  
"""  
instead of the marimo output.

## Ideal Gas Law: symbolic rearrangement

"""
<p align="center">
  <img src="docs/public/piston.gif" alt="Clicking the radio button changes which variable in the ideal gas law is unknown. SymPy solves for that unknown before passing the values of the knowns defined by the sliders. Changing the radio button and sliders updates the piston and symbolic evaluation in real time." width="620">
</p>

Open the [Getting started tutorial](https://bedrock-engineer.github.io/symeval/getting-started.html) on the docs website, or <open in molab badge> for the live, interactive version.  
"""  
instead of the marimo output.

## Feedback & contributing

Found a bug or have a feature request? [Open an issue](https://github.com/bedrock-engineer/symeval/issues), pull requests are welcome too.

Want to add a worked example? See [`CONTRIBUTING.md`](CONTRIBUTING.md) for the dev setup, the docs dev server, and how to add a notebook.

The package is a single marimo notebook (`symeval_mo.py`) with `## EXPORT`-marked cells extracted into `src/symeval/` via [mobuild](https://github.com/koaning/mobuild); see [`CLAUDE.md`](CLAUDE.md) for the project layout and [`RELEASING.md`](RELEASING.md) for the release workflow.

## Inspiration

From index.qmd?

## Authors

Built and maintained by the [Bedrock.engineer](https://bedrock.engineer)s ([Joost Gevaert](https://github.com/JoostGevaert) and [Jules Blom](https://github.com/JulesBlm)).

## License

Apache License 2.0, see [LICENSE](LICENSE).
