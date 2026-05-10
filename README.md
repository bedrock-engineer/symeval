# symeval

Write a [`sympy`](https://docs.sympy.org) expression, fill in [`pint`](https://pint.readthedocs.io/) quantities, and get the full derivation, that is (1) formula, (2) substituted values with units, and (3) the result with unit — rendered as LaTeX in your [`marimo`](https://docs.marimo.io) or Jupyter notebook.

- ✨ **Crystal-clear** - shows the full derivation: formula, values with units, and result of any expression
- 🐍 **Pure Python** - integrate into your *interactive* notebooks and other Python code, no special syntax, no cell magic, no Domain-Specific Language (DSL)
- 📏 **Unit-aware** - `pint` quantities carry units through every step and convert to your chosen output unit
- 🧮 **Sympy-native** - use symbolic math to derive or rearrange your formula first, then evaluate symbolicly
- 📊 **DataFrame-ready** - use `sympy.Expr.quantity_evalf()` on a `DataFrame` to calculate the values of a new column in a unit-aware manner

```sh
pip install symeval
```

---

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
&= \frac{\medspace-680\ \mathrm{kN}}{\medspace10580\ \mathrm{mm}^{2}} \\
\sigma &= -6.43\times 10^{7}\ \mathrm{Pa} = -64.27\ \mathrm{MPa}
\end{align*}$$

You can also build the `sympy` expression first and call `.sym_evalf()` as a method — useful when you want to do symbolic math before filling in numbers:

```python
from sympy import Symbol
from pint import Quantity

f_sym = Symbol("F")
a_sym = Symbol("A")
sigma_expr = f_sym / a_sym

f_q = Quantity(-680, "kN")
a_q = Quantity(10_580, "mm^2")
```

Pass `decimals=` to control precision and `mode=` to choose the rendering style. `mode="verbose"` adds an extra line showing all values converted to SI base units:

```python
sigma_expr.sym_evalf(
    subs={f_sym: f_q, a_sym: a_q},
    output_symbol=r"\sigma",
    output_unit="MPa",
    decimals=2,
    mode="verbose",
)
```

$$\begin{align*}
\sigma &= \frac{F}{A} \\
&= \frac{\medspace-680\ \mathrm{kN}}{\medspace10580\ \mathrm{mm}^{2}} \\
&= \frac{\medspace-6.800\times 10^{5}\ \mathrm{N}}{\medspace1.058\times 10^{-2}\ \mathrm{m}^{2}} \\
\sigma &= -6.43\times 10^{7}\ \mathrm{Pa} = -64.27\ \mathrm{MPa}
\end{align*}$$

`mode="one_line"` collapses the derivation onto a single line:

```python
sigma_expr.sym_evalf(
    subs={f_sym: f_q, a_sym: a_q},
    output_symbol=r"\sigma",
    output_unit="MPa",
    decimals=1,
    mode="one_line",
)
```

$$\sigma = \frac{F}{A} = \frac{\medspace-680\ \mathrm{kN}}{\medspace10580\ \mathrm{mm}^{2}} = -64.3\ \mathrm{MPa}$$

---

## Ideal Gas Law: Symbolic Rearrangement

Starting from $PV = nRT$, use `sympy.solve` to rearrange the equation symbolically for any variable, then feed the result straight into `sym_evalf`:

```python
import sympy
from sympy.physics.units import molar_gas_constant
import sympy.physics.units as spu
from sympy.physics.units.util import convert_to
from pint import Quantity
from symeval import sym_evalf

P, V, n, T, R = sympy.symbols("P V n T R")

# Rearrange symbolically — no hardcoding which variable to solve for
ideal_gas_law = sympy.Eq(P * V, n * R * T)
solution = sympy.solve(ideal_gas_law, P)[0]

# Pull R from sympy — no hardcoded constant
R_si = convert_to(molar_gas_constant, [spu.joule, spu.mol, spu.kelvin])
R_q = Quantity(float(R_si.args[0]), "J/(mol*K)")

solution.sym_evalf(
    subs={R: R_q, V: Quantity(22.4, "L"), n: Quantity(1.0, "mol"), T: Quantity(273.15, "K")},
    output_symbol=P,
    output_unit="kPa",
    decimals=2,
)
```

**Rearranged:** $P = \dfrac{R T n}{V}$

$$\begin{align*}
P &= \frac{R T n}{V} \\
&= \frac{\medspace8.314\ \frac{\mathrm{J}}{\left(\mathrm{K} \cdot \mathrm{mol}\right)} \medspace273.15\ \mathrm{K} \medspace1\ \mathrm{mol}}{\medspace22.4\ \mathrm{l}} \\
P &= 1.01\times 10^{5}\ \mathrm{Pa} = 101.39\ \mathrm{kPa}
\end{align*}$$

> **In [marimo](https://marimo.io):** add a `mo.ui.radio` to let the user pick which variable to solve for — the symbolic rearrangement and evaluation both update reactively.

---

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
&= \frac{\medspace-680\ \mathrm{kN}}{\medspace10580\ \mathrm{mm}^{2}} \\
\sigma &= -6.4\times 10^{7}\ \mathrm{Pa} = -64.3\ \mathrm{MPa}
\end{align*}$$

---

## Inspiration

- [handcalcs](https://github.com/connorferster/handcalcs) — renders Python calculation code as LaTeX in Jupyter
- [CalcPad](https://calcpad-ce.org) — engineering calculations DSL with symbolic/numeric workflow
- Bret Victor's [Explorable Explanations](https://worrydream.com/ExplorableExplanations/)
