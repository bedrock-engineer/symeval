# symeval

Write a [`sympy`](https://docs.sympy.org) expression, fill in [`pint`](https://pint.readthedocs.io/) quantities, and get the full derivation, that is (1) formula, (2) substituted values with units, and (3) the result with unit — rendered as LaTeX in your [`marimo`](https://docs.marimo.io) or Jupyter notebook.

- ✨ **Crystal-clear** — shows the full derivation: formula, values with units, and result
- 🐍 **Pure Python** — drop into your *interactive* notebooks and other Python code, no special syntax, no cell magic, no Domain-Specific Language (DSL)
- 📏 **Unit-aware** — `pint` quantities carry units through every step and convert to your chosen output unit
- 🧮 **Sympy-native** — rearrange or simplify your formula symbolically first, then evaluate
- 📊 **DataFrame-ready** — use `quantity_evalf()` to compute a new unit-aware column on a `DataFrame`

```sh
pip install symeval
```

## Axial stress under a compressive force

```python
from pint import Quantity
from sympy import Symbol
from symeval import sym_evalf

sigma = sym_evalf(
    expr=Symbol("F") / Symbol("A"),
    subs={Symbol("F"): Quantity(-680, "kN"), Symbol("A"): Quantity(10_580, "mm^2")},
    output_symbol=r"\sigma",
    output_unit="MPa",
    decimals=2,
)
```

$$\begin{align*}
\sigma &= \frac{F}{A} \\
&= \frac{\,-680\ \mathrm{kN}}{\,10580\ \mathrm{mm}^{2}} \\
\sigma &= -6.43\times 10^{7}\ \mathrm{Pa} = -64.27\ \mathrm{MPa}
\end{align*}$$

You can also build the `sympy` expression first and call `.sym_evalf()` as a method — useful when you want to do symbolic math before filling in numbers. Pass `mode=` to choose the rendering style; `mode="verbose"` adds an extra line showing all values converted to SI base units:

```python
f_sym, a_sym = Symbol("F"), Symbol("A")
sigma_expr = f_sym / a_sym

sigma_expr.sym_evalf(
    subs={f_sym: Quantity(-680, "kN"), a_sym: Quantity(10_580, "mm^2")},
    output_symbol=r"\sigma",
    output_unit="MPa",
    decimals=2,
    mode="verbose",
)
```

$$\begin{align*}
\sigma &= \frac{F}{A} \\
&= \frac{\,-680\ \mathrm{kN}}{\,10580\ \mathrm{mm}^{2}} \\
&= \frac{\,-6.800\times 10^{5}\ \mathrm{N}}{\,1.058\times 10^{-2}\ \mathrm{m}^{2}} \\
\sigma &= -6.43\times 10^{7}\ \mathrm{Pa} = -64.27\ \mathrm{MPa}
\end{align*}$$

`mode="one_line"` collapses the derivation onto a single line:

```python
sigma_expr.sym_evalf(
    subs={f_sym: Quantity(-680, "kN"), a_sym: Quantity(10_580, "mm^2")},
    output_symbol=r"\sigma",
    output_unit="MPa",
    decimals=1,
    mode="one_line",
)
```

$$\sigma = \frac{F}{A} = \frac{\,-680\ \mathrm{kN}}{\,10580\ \mathrm{mm}^{2}} = -64.3\ \mathrm{MPa}$$

## `quantity_evalf()` on a DataFrame

`quantity_evalf` is the numeric-only sibling of `sym_evalf` — same unit-aware evaluation, no LaTeX overhead. It's useful for applying a formula across every row of a DataFrame:

```python
import polars as pl
from pint import Quantity
from sympy import Symbol
from symeval import quantity_evalf

f_sym, a_sym = Symbol("F"), Symbol("A")
sigma_expr = f_sym / a_sym

members = pl.DataFrame({
    "member_type": ["column", "column", "brace", "strut", "tie"],
    "section":     ["W14x90", "HSS8x8x5/8", "HSS6x6x3/8", "L4x4", "C8x11.5"],
    "F_kN":        [-720.0, -680.0, 340.0, -110.0, 250.0],
    "A_mm2":       [17_100.0, 10_580.0, 4_890.0, 1_870.0, 2_168.0],
})

def stress_MPa(row):
    return quantity_evalf(
        sigma_expr,
        subs={f_sym: Quantity(row["F_kN"], "kN"), a_sym: Quantity(row["A_mm2"], "mm^2")},
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

Then use `sym_evalf` to show the full derivation for any row you want to inspect:

```python
sigma_expr.sym_evalf(
    subs={f_sym: Quantity(-680, "kN"), a_sym: Quantity(10_580, "mm^2")},
    output_symbol=r"\sigma",
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

A worked example from CSA S16-17. Each `sym_evalf` result feeds into the next — `F_e` into $\lambda$, $\lambda$ into $C_r$, $C_r$ into $DCR$ — so the LaTeX rendering captures the full audit trail of a multi-step engineering check:

$$F_{e} = \frac{\pi^{2} E r_{y}^{2}}{L^{2} k^{2}} = \frac{\pi^{2} \,200\ \mathrm{GPa} \,\left(76.1\ \mathrm{mm}\right)^{2}}{\,\left(6.5\ \mathrm{m}\right)^{2} \,1^{2}} = 0.271\ \mathrm{GPa}$$

$$\lambda = \left(\frac{F_{y}}{F_{e}}\right)^{n} = \left(\frac{\,400\ \mathrm{MPa}}{\,0.2706\ \mathrm{GPa}}\right)^{\,1.34} = 1.689$$

$$C_{r} = A F_{y} \phi_{s} \left(\lambda + 1\right)^{- \frac{1}{n}} = \,10580\ \mathrm{mm}^{2} \,400\ \mathrm{MPa} \,0.85 \left(\,1.6886 + 1\right)^{- \frac{1}{\,1.34}} = 1.720\ \mathrm{MN}$$

$$DCR = \frac{C_{f}}{C_{r}} = \frac{\,680\ \mathrm{kN}}{\,1.7196\ \mathrm{MN}} = 0.395$$

See `symeval_mo.py` for the full reactive marimo notebook with input UIs.

## Ideal Gas Law: symbolic rearrangement

Starting from $PV = nRT$, `sympy.solve` rearranges the equation symbolically for any variable, then the resulting expression feeds straight into `sym_evalf`:

$$\begin{align*}
P &= \frac{R T n}{V} \\
&= \frac{\,8.314\ \frac{\mathrm{J}}{\left(\mathrm{K} \cdot \mathrm{mol}\right)} \,273.15\ \mathrm{K} \,1\ \mathrm{mol}}{\,22.4\ \mathrm{l}} \\
P &= 1.01\times 10^{5}\ \mathrm{Pa} = 101.39\ \mathrm{kPa}
\end{align*}$$

See `symeval_mo.py` for the full reactive marimo notebook with input UIs.

## Author

Built and maintained by [Joost Gevaert](https://github.com/JoostGevaert) at [Bedrock](https://bedrock.engineer).

## Feedback & contributing

Found a bug or have a feature request? [Open an issue](https://github.com/bedrock-engineer/symeval/issues) — pull requests are welcome too. The package is a single marimo notebook (`symeval_mo.py`) with `## EXPORT`-marked cells extracted into `src/symeval/` via [mobuild](https://github.com/koaning/mobuild); see [`CLAUDE.md`](CLAUDE.md) for the project layout and [`RELEASING.md`](RELEASING.md) for the release workflow.

## Inspiration

- [handcalcs](https://github.com/connorferster/handcalcs) — renders Python calculation code as LaTeX in Jupyter
- [CalcPad](https://calcpad-ce.org) — engineering calculations DSL with symbolic/numeric workflow
- Bret Victor's [Explorable Explanations](https://worrydream.com/ExplorableExplanations/)

## License

Apache License 2.0 — see [LICENSE](LICENSE).
