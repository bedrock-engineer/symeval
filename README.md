# symeval

Write a [`sympy`](https://docs.sympy.org) equation, fill in [`pint`](https://pint.readthedocs.io/) quantities, and get the full working, that is (1) the symbolic form, (2) the substituted form with units, and (3) the result with its unit, rendered as LaTeX in your [`marimo`](https://docs.marimo.io) or Jupyter notebook.

- ✨ **Crystal-clear**: shows the full working, that is symbolic form, substituted form, and result
- 🐍 **Pure Python**: drop into your *interactive* notebooks and other Python code, no special syntax, no cell magic, no Domain-Specific Language (DSL)
- 📏 **Unit-aware**: `pint` quantities carry units through every step and convert to your chosen output unit
- 🧮 **Sympy-native**: rearrange or simplify your formula symbolically first, then evaluate
- 📊 **DataFrame-ready**: use `quantity_evalf()` to compute a new unit-aware column on a `DataFrame`

```sh
pip install symeval
```

📖 **[Documentation](https://bedrock-engineer.github.io/symeval)**

## Axial stress under a compressive force

Define the formula as a `sympy.Eq`, fill in `pint` quantities, and `sym_evalf`
renders the working. The output symbol is taken from the equation, so you do not
pass it separately:

```python
from pint import Quantity
from sympy import Eq, Symbol
from symeval import sym_evalf

axial_stress = Eq(Symbol(r"\sigma"), Symbol("F") / Symbol("A"))

sym_evalf(
    axial_stress,
    subs={Symbol("F"): Quantity(-680, "kN"), Symbol("A"): Quantity(10_580, "mm^2")},
    output_unit="MPa",
    decimals=2,
)
```

$$\begin{align*}
\sigma &= \frac{F}{A} \\
&= \frac{\,-680\ \mathrm{kN}}{\,10580\ \mathrm{mm}^{2}} \\
\sigma &= -6.43\times 10^{7}\ \mathrm{Pa} = -64.27\ \mathrm{MPa}
\end{align*}$$

You can also call `.sym_evalf()` as a method on the equation. Pass `mode=` to
choose the rendering style; `mode="verbose"` adds an extra line to the working,
showing all values converted to SI base units:

```python
axial_stress = Eq(Symbol(r"\sigma"), Symbol("F") / Symbol("A"))
fa = {Symbol("F"): Quantity(-680, "kN"), Symbol("A"): Quantity(10_580, "mm^2")}

axial_stress.sym_evalf(subs=fa, output_unit="MPa", decimals=2, mode="verbose")
```

$$\begin{align*}
\sigma &= \frac{F}{A} \\
&= \frac{\,-680\ \mathrm{kN}}{\,10580\ \mathrm{mm}^{2}} \\
&= \frac{\,-6.800\times 10^{5}\ \mathrm{N}}{\,1.058\times 10^{-2}\ \mathrm{m}^{2}} \\
\sigma &= -6.43\times 10^{7}\ \mathrm{Pa} = -64.27\ \mathrm{MPa}
\end{align*}$$

`mode="one_line"` collapses the working onto a single line:

```python
axial_stress.sym_evalf(subs=fa, output_unit="MPa", decimals=1, mode="one_line")
```

$$\sigma = \frac{F}{A} = \frac{\,-680\ \mathrm{kN}}{\,10580\ \mathrm{mm}^{2}} = -64.3\ \mathrm{MPa}$$

## `quantity_evalf()` on a DataFrame

`quantity_evalf` is the numeric-only sibling of `sym_evalf`, that is the same
unit-aware evaluation without the working. It takes an expression rather than an
equation, so pass the equation's right-hand side (`axial_stress.rhs`). This makes
it useful for applying a formula across every row of a DataFrame:

```python
import polars as pl
from pint import Quantity
from sympy import Eq, Symbol
from symeval import quantity_evalf

axial_stress = Eq(Symbol(r"\sigma"), Symbol("F") / Symbol("A"))

members = pl.DataFrame({
    "member_type": ["column", "column", "brace", "strut", "tie"],
    "section":     ["W14x90", "HSS8x8x5/8", "HSS6x6x3/8", "L4x4", "C8x11.5"],
    "F_kN":        [-720.0, -680.0, 340.0, -110.0, 250.0],
    "A_mm2":       [17_100.0, 10_580.0, 4_890.0, 1_870.0, 2_168.0],
})

def stress_MPa(row):
    return quantity_evalf(
        axial_stress.rhs,
        subs={Symbol("F"): Quantity(row["F_kN"], "kN"), Symbol("A"): Quantity(row["A_mm2"], "mm^2")},
        output_unit="MPa",
    ).magnitude

members_with_stress = members.with_columns(
    pl.struct(["F_kN", "A_mm2"])
    .map_elements(stress_MPa, return_dtype=pl.Float64)
    .alias("sigma_MPa")
)
```

| member_type | section | F_kN | A_mm2 | sigma_MPa |
| --- | --- | --- | --- | --- |
| column | W14x90 | -720.00 | 17100.00 | -42.11 |
| column | HSS8x8x5/8 | -680.00 | 10580.00 | -64.27 |
| brace | HSS6x6x3/8 | 340.00 | 4890.00 | 69.53 |
| strut | L4x4 | -110.00 | 1870.00 | -58.82 |
| tie | C8x11.5 | 250.00 | 2168.00 | 115.31 |

Then use `sym_evalf` to show the full working for any row you want to inspect:

```python
axial_stress.sym_evalf(
    subs={Symbol("F"): Quantity(-680, "kN"), Symbol("A"): Quantity(10_580, "mm^2")},
    output_unit="MPa",
    decimals=1,
)
```

$$\begin{align*}
\sigma &= \frac{F}{A} \\
&= \frac{\,-680\ \mathrm{kN}}{\,10580\ \mathrm{mm}^{2}} \\
\sigma &= -6.4\times 10^{7}\ \mathrm{Pa} = -64.3\ \mathrm{MPa}
\end{align*}$$

## Axial resistance of a steel HSS member

A worked example from CSA S16-17. Each symbolic evaluation is chained into the
next, that is `F_e` into $\lambda$, $\lambda$ into $C_r$, $C_r$ into $DCR$, so the
working captures every step of a multi-step engineering check:

$$F_{e} = \frac{\pi^{2} E r_{y}^{2}}{L^{2} k^{2}} = \frac{\pi^{2} \,200\ \mathrm{GPa} \,\left(76.1\ \mathrm{mm}\right)^{2}}{\,\left(6.5\ \mathrm{m}\right)^{2} \,1^{2}} = 0.271\ \mathrm{GPa}$$

$$\lambda = \left(\frac{F_{y}}{F_{e}}\right)^{n} = \left(\frac{\,400\ \mathrm{MPa}}{\,0.2706\ \mathrm{GPa}}\right)^{\,1.34} = 1.689$$

$$C_{r} = A F_{y} \phi_{s} \left(\lambda + 1\right)^{- \frac{1}{n}} = \,10580\ \mathrm{mm}^{2} \,400\ \mathrm{MPa} \,0.85 \left(\,1.6886 + 1\right)^{- \frac{1}{\,1.34}} = 1.720\ \mathrm{MN}$$

$$DCR = \frac{C_{f}}{C_{r}} = \frac{\,680\ \mathrm{kN}}{\,1.7196\ \mathrm{MN}} = 0.395$$

See `symeval_mo.py` for the full reactive marimo notebook with input UIs.

## Ideal Gas Law: symbolic rearrangement

Starting from $PV = nRT$ as a `sympy.Eq`, `sym_evalf` solves for the single
unknown and evaluates, so you never write the rearranged form by hand:

$$\begin{align*}
P &= \frac{R T n}{V} \\
&= \frac{\,8.314\ \frac{\mathrm{J}}{\left(\mathrm{K} \cdot \mathrm{mol}\right)} \,273.15\ \mathrm{K} \,1\ \mathrm{mol}}{\,22.4\ \mathrm{l}} \\
P &= 1.01\times 10^{5}\ \mathrm{Pa} = 101.39\ \mathrm{kPa}
\end{align*}$$

See `symeval_mo.py` for the full reactive marimo notebook with input UIs.

## Author

Built and maintained by [Joost Gevaert](https://github.com/JoostGevaert) at [Bedrock](https://bedrock.engineer).

## Feedback & contributing

Found a bug or have a feature request? [Open an issue](https://github.com/bedrock-engineer/symeval/issues), pull requests are welcome too. Want to add a worked example? See [`CONTRIBUTING.md`](CONTRIBUTING.md) for the dev setup, the docs dev server, and how to add a notebook. The package is a single marimo notebook (`symeval_mo.py`) with `## EXPORT`-marked cells extracted into `src/symeval/` via [mobuild](https://github.com/koaning/mobuild); see [`CLAUDE.md`](CLAUDE.md) for the project layout and [`RELEASING.md`](RELEASING.md) for the release workflow.

## Inspiration

- [handcalcs](https://github.com/connorferster/handcalcs), renders Python calculation code as LaTeX in Jupyter
- [CalcPad](https://calcpad-ce.org), engineering calculations DSL with symbolic/numeric workflow
- Bret Victor's [Explorable Explanations](https://worrydream.com/ExplorableExplanations/)

## License

Apache License 2.0, see [LICENSE](LICENSE).
