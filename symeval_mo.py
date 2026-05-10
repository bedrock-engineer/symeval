# /// script
# requires-python = ">=3.12"
# dependencies = [
#     "marimo",
#     "pint==0.25.3",
#     "polars==1.40.1",
#     "pytest==9.0.3",
#     "sympy==1.14.0",
# ]
# ///

import marimo

__generated_with = "0.23.5"
app = marimo.App(width="columns")


@app.cell(column=0, hide_code=True)
def _(mo):
    mo.md(r"""
    # symeval

    Symbolic evaluation for engineering calculations.

    Renders the three-step chain:
    **symbolic → numbers with units → result** as LaTeX.
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Axial stress under a compressive force
    """)
    return


@app.cell
def _(sym_evalf):
    from pint import Quantity
    from sympy import Symbol
    # from symeval import sym_evalf

    sigma = sym_evalf(
        expr=Symbol("F") / Symbol("A"),
        subs={Symbol("F"): Quantity(-680, "kN"), Symbol("A"): Quantity(10_580, "mm^2")},
        output_symbol=r"\sigma",
        output_unit="MPa",
    )
    sigma
    return Quantity, Symbol


@app.cell
def _(Symbol):
    # You can also first specify a sympy expression:
    f_sym = Symbol("F")
    a_sym = Symbol("A")
    sigma_expr = f_sym / a_sym
    sigma_expr
    return a_sym, f_sym, sigma_expr


@app.cell
def _(Quantity, a_sym, f_sym, sigma_expr):
    # And then call sym_evalf as a method on that expression. Moreover, you can
    # specify the number of decimal places of your result, and the render mode:
    # verbose: adds an extra line showing all values converted to SI base units.
    f_q = Quantity(-680, "kN")
    a_q = Quantity(10_580, "mm^2")
    sigma_expr.sym_evalf(
        subs={f_sym: f_q, a_sym: a_q},
        output_symbol=r"\sigma",
        output_unit="MPa",
        decimals=2,
        mode="verbose",
    )
    return a_q, f_q


@app.cell
def _(a_q, a_sym, f_q, f_sym, sigma_expr):
    # one_line: collapse the derivation onto a single line.
    sigma_expr.sym_evalf(
        subs={f_sym: f_q, a_sym: a_q},
        output_symbol=r"\sigma",
        output_unit="MPa",
        decimals=1,
        mode="one_line",
    )
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## `quantity_evalf()` on a `DataFrame`

    Now suppose I have done a structural analysis, which gave me the axial forces acting on the members, and now I want to calculate what the resulting axial stresses on these members are. So, let's:

    1. create a `polars.DataFrame` with the forces and cross-sectional areas of these members;
    2. calculate the axial stresses using `quantity_evalf()` on the `DataFrame`;
    3. symbolicly evaluate the axial stress in the member which we select from a `marimo.ui.table` widget.
    """)
    return


@app.cell
def _(Quantity, a_q, a_sym, f_q, f_sym, quantity_evalf, sigma_expr):
    import marimo as mo
    import polars as pl
    # from symeval import quantity_evalf

    # 1. Forces are in kN, areas in mm^2.
    members = pl.DataFrame(
        {
            "member_type": ["column", "column", "brace", "strut", "tie"],
            "section": ["W14x90", "HSS8x8x5/8", "HSS6x6x3/8", "L4x4", "C8x11.5"],
            "F_kN": [-720.0, f_q.magnitude, 340.0, -110.0, 250.0],
            "A_mm2": [17_100.0, a_q.magnitude, 4_890.0, 1_870.0, 2_168.0],
        }
    )


    # 2. Vectorise via polars: build a Quantity per row, evaluate to MPa, take the
    # magnitude. Returning the bare float keeps the column polars-native.
    def _stress_MPa(row):
        return quantity_evalf(
            expr=sigma_expr,
            subs={
                f_sym: Quantity(row["F_kN"], "kN"),
                a_sym: Quantity(row["A_mm2"], "mm^2"),
            },
            output_unit="MPa",
        ).magnitude

    # Apply the vectorized function to the polars dataframe to calculate the axial stresses in the members.
    members_with_stress = members.with_columns(
        pl.struct(["F_kN", "A_mm2"])
        .map_elements(_stress_MPa, return_dtype=pl.Float64)
        .alias("sigma_MPa")
    )


    # 3a. Create a marimo ui element in which you can select the member for which
    # you want to symbolicly evaluate the calculation.
    selected_member_to_symeval = mo.ui.table(
        members_with_stress, selection="single", initial_selection=[1]
    )
    selected_member_to_symeval
    return mo, selected_member_to_symeval


@app.cell(hide_code=True)
def _(Quantity, a_sym, f_sym, selected_member_to_symeval, sigma_expr):
    # 3b. Do the symbolic evaluation for the selected member
    _sel_row = selected_member_to_symeval.value
    sigma_expr.sym_evalf(
        subs={
            f_sym: Quantity(_sel_row["F_kN"][0], "kN"),
            a_sym: Quantity(_sel_row["A_mm2"][0], "mm^2"),
        },
        output_symbol=r"\sigma",
        output_unit="MPa",
        decimals=1,
    )
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Axial Resistance of Steel HSS Member
    As per CSA S16-17

    This is the example calculation that Connor Ferster, the author of [`handcalcs`](https://github.com/connorferster/handcalcs), shows in [this "Engineering Calculations: Handcalcs-on-Jupyter vs. Excel" YouTube tutorial](https://www.youtube.com/watch?v=n9Uzy3Eb-XI).
    """)
    return


@app.cell(hide_code=True)
def _(a_q, f_q, mo, sympy):
    (
        compressive_force,
        beam_length,
        effective_length_factor,
        elastic_modulus,
        yield_strength,
        strain_hardening_exponent,
        strength_reduction_factor,
        cross_sectional_area,
        radius_gyration,
    ) = sympy.symbols(r"C_f L k E F_y n \phi_s A r_y")

    input_uis = mo.ui.dictionary(
        {
            "Compressive force": mo.ui.number(value=-f_q.magnitude),
            "Beam length": mo.ui.number(value=6.5, step=0.1),
            "Effective length factor": mo.ui.number(value=1, step=0.1),
            "Elastic modulus": mo.ui.number(value=200),
            "Yield strength": mo.ui.number(value=400),
            "Strain-hardening exponent": mo.ui.number(value=1.34, step=0.01),
            "Strength reduction factor": mo.ui.number(value=0.85, step=0.05),
            "Cross-sectional area": mo.ui.number(value=a_q.magnitude),
            "Radius of gyration about the y-axis": mo.ui.number(
                value=76.1, step=0.1
            ),
        }
    )

    input_table = [
        {"section": "Loads"},
        {
            "name": "Compressive force",
            "symbol": compressive_force,
            "unit": "kN",
        },
        {"section": "Member geometry"},
        {
            "name": "Beam length",
            "symbol": beam_length,
            "unit": "m",
        },
        {
            "name": "Effective length factor",
            "symbol": effective_length_factor,
        },
        {"section": "Material properties"},
        {
            "name": "Elastic modulus",
            "symbol": elastic_modulus,
            "unit": "GPa",
        },
        {
            "name": "Yield strength",
            "symbol": yield_strength,
            "unit": "MPa",
        },
        {
            "name": "Strain-hardening exponent",
            "symbol": strain_hardening_exponent,
        },
        {
            "name": "Strength reduction factor",
            "symbol": strength_reduction_factor,
        },
        {"section": "Member section properties"},
        {
            "name": "Cross-sectional area",
            "symbol": cross_sectional_area,
            "unit": "mm^2",
        },
        {
            "name": "Radius of gyration about the y-axis",
            "symbol": radius_gyration,
            "unit": "mm",
        },
    ]


    def _table_row(s):
        if "section" in s:
            return f"| **{s['section']}** |  |  |  |  |"
        unit = f"${s['unit']}$" if s.get("unit") else ""
        return f"| {s['name']} | ${s['symbol']}$ | = | {input_uis[s['name']]} | {unit} |"


    mo.md(
        "### Inputs\n"
        "|     |     |     |     |     |\n"
        "|--------------|--------|---|-----|---|\n"
        + "\n".join(_table_row(s) for s in input_table)
    )
    return (
        beam_length,
        compressive_force,
        cross_sectional_area,
        effective_length_factor,
        elastic_modulus,
        input_table,
        input_uis,
        radius_gyration,
        strain_hardening_exponent,
        strength_reduction_factor,
        yield_strength,
    )


@app.cell(hide_code=True)
def _(axial_resistance, dcr, euler_buckling_stress, lambda_factor, mo):
    mo.vstack(
        [
            mo.md("### Calculation"),
            mo.hstack(
                [
                    mo.md("Euler buckling stress"),
                    mo.md(rf"$\displaystyle {euler_buckling_stress.latex}$"),
                ],
                widths=[1, 4],
                align="center",
                gap=2,
            ),
            mo.hstack(
                [
                    mo.md(r"$\lambda$ factor"),
                    mo.md(rf"$\displaystyle {lambda_factor.latex}$"),
                ],
                widths=[1, 4],
                align="center",
                gap=2,
            ),
            mo.hstack(
                [
                    mo.md("Axial resistance"),
                    mo.md(rf"$\displaystyle {axial_resistance.latex}$"),
                ],
                widths=[1, 4],
                align="center",
                gap=2,
            ),
            mo.hstack(
                [
                    mo.md("Demand capacity ratio"),
                    mo.md(rf"$\displaystyle {dcr.latex}$"),
                ],
                widths=[1, 4],
                align="center",
                gap=2,
            ),
        ],
        gap=2,
    )
    return


@app.cell
def _(
    Quantity,
    beam_length,
    compressive_force,
    cross_sectional_area,
    effective_length_factor,
    elastic_modulus,
    input_table,
    input_uis,
    radius_gyration,
    strain_hardening_exponent,
    strength_reduction_factor,
    sympy,
    yield_strength,
):
    # Create a dictionary with `sympy.Symbol` as keys and the input values as values
    symbolic_quantities = {
        s["symbol"]: Quantity(input_uis[s["name"]].value, s.get("unit"))
        for s in input_table
        if "name" in s
    }

    # Define the Euler buckling stress sympy expression
    euler_buckling_expr = (sympy.pi**2 * elastic_modulus) / (
        (beam_length * effective_length_factor / radius_gyration) ** 2
    )
    # Symbolicly evaluate the Euler buckling stress
    euler_buckling_stress = euler_buckling_expr.sym_evalf(
        subs=symbolic_quantities,
        output_symbol=sympy.Symbol("F_e"),
        output_unit="GPa",
        decimals=3,
        mode="one_line",
    )
    # Add the resulting Euler buckling stress to the dictionary with symbolic quantities
    # such that it can be used in subsequent `.sym_evalf`s
    symbolic_quantities[euler_buckling_stress.symbol] = euler_buckling_stress.quantity

    # Same for the lambda factor: def expression; sym_evalf; add result to symbolic quantities dict
    lambda_factor_expr = (
        sympy.sqrt(yield_strength / euler_buckling_stress.symbol)
    ) ** (2 * strain_hardening_exponent)
    lambda_factor = lambda_factor_expr.sym_evalf(
        subs=symbolic_quantities,
        output_symbol=sympy.Symbol(r"\lambda"),
        decimals=3,
        mode="one_line",
    )
    symbolic_quantities[lambda_factor.symbol] = lambda_factor.quantity

    # Axial resistance
    axial_resistance_expr = (
        strength_reduction_factor * cross_sectional_area * yield_strength
    ) / ((1 + lambda_factor.symbol) ** (1 / strain_hardening_exponent))
    axial_resistance = axial_resistance_expr.sym_evalf(
        subs=symbolic_quantities,
        output_symbol=sympy.Symbol("C_r"),
        output_unit="MN",
        decimals=3,
        mode="one_line",
    )
    symbolic_quantities[axial_resistance.symbol] = axial_resistance.quantity

    # Demand capacity ratio
    dcr_expr = compressive_force / axial_resistance.symbol
    dcr = dcr_expr.sym_evalf(
        subs=symbolic_quantities,
        output_symbol=sympy.Symbol("DCR"),
        decimals=3,
        mode="one_line",
    )
    symbolic_quantities[dcr.symbol] = dcr.quantity
    return axial_resistance, dcr, euler_buckling_stress, lambda_factor


@app.cell(column=1, hide_code=True)
def _(mo):
    mo.md(r"""
    # Implementation
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    Cells marked with `## EXPORT` are extracted into the Python package via
    [`mobuild`](https://github.com/koaning/mobuild).
    """)
    return


@app.cell
def _():
    ## EXPORT

    import textwrap
    from dataclasses import dataclass, field
    from typing import Literal

    import pint
    import sympy
    from sympy import latex

    return Literal, latex, pint, sympy


@app.cell
def _(Literal, latex, pint, sympy):
    ## EXPORT

    def _quantity_to_sympy_base(quantity: pint.Quantity) -> sympy.Expr:
        """Convert a pint quantity to a sympy expression in base SI units.

        Dimensionless quantities return their bare magnitude (a Python float).
        """
        if quantity.dimensionality == {}:
            return quantity.magnitude
        base = quantity.to_base_units()
        sympy_units = sympy.sympify(f"{base.units:~D}")
        return base.magnitude * sympy_units

    def quantity_evalf(
        expr: sympy.Expr,
        subs: dict[sympy.Symbol, pint.Quantity] | None = None,
        output_unit: str | pint.Unit | None = None,
        **evalf_kwargs,
    ) -> pint.Quantity:
        """Numerical evaluation of a sympy expression with unit-aware substitutions.

        Mirrors `sympy.Expr.evalf`'s signature. Any extra keyword arguments are
        captured by Python's `**evalf_kwargs` (a standard mechanism for
        collecting unmatched kwargs into a dict) and forwarded verbatim to
        `expr.evalf(...)` — so `n`, `maxn`, `chop`, `strict`, `quiet`, and
        `verbose` all work without being listed here individually.

        Args:
            expr (sympy.Expr): The sympy expression to evaluate.
            subs (dict[sympy.Symbol, pint.Quantity] | None): Mapping from
                `sympy.Symbol` to `pint.Quantity` (or a scalar for dimensionless
                inputs). Same shape as sympy.evalf's `subs` kwarg, but values
                carry units. Defaults to None (no substitutions).
            output_unit (str | pint.Unit | None): Target pint unit for the
                result (e.g. `"MPa"` or `ureg.MPa`). If `None`, the result is
                returned in SI base units. Defaults to None. The result's
                registry is the registry of the input `pint.Quantity` values
                in `subs`; with empty subs (or all-scalar subs),
                `pint.get_application_registry()` is used as a fallback.
            **evalf_kwargs: Forwarded verbatim to `expr.evalf(...)`. Useful
                kwargs include `n` (digits of precision), `chop` (round tiny
                terms to zero), and `strict` (raise instead of returning an
                unevaluated result).

        Returns:
            pint.Quantity: The computed quantity — in `output_unit` if given,
                else in SI base units.
        """
        subs = subs or {}
        target_ureg = next(
            (q._REGISTRY for q in subs.values() if isinstance(q, pint.Quantity)),
            pint.get_application_registry(),
        )
        base_subs = {sym: _quantity_to_sympy_base(q) for sym, q in subs.items()}
        result_value = expr.evalf(subs=base_subs, **evalf_kwargs)
        output_quantity = target_ureg(f"{result_value}")
        if output_unit is not None:
            output_quantity = output_quantity.to(output_unit)
        return output_quantity

    def _strip_si_prefixes(quantity: pint.Quantity) -> pint.Quantity:
        """Convert a quantity to its SI-prefix-free equivalent (kN -> N, MPa -> Pa, mm -> m).

        `kg` is left as-is because it is itself the SI base unit for mass — even
        though pint internally represents it as kilo*gram.
        """
        if quantity.dimensionless:
            return quantity
        ureg = quantity._REGISTRY
        target = {}
        for unit_name, exponent in dict(quantity.units._units).items():
            parses = ureg.parse_unit_name(unit_name)
            # Prefer an unprefixed parse (e.g. \'Pa\' has both (\'\', \'pascal\', \'\') and (\'peta\', \'year\', \'\')).
            base = next((b for prefix, b, _ in parses if prefix == ""), None)
            if base is None and parses:
                # All parses are prefixed (e.g. \'kN\' -> (\'kilo\', \'newton\', \'\')).
                prefix, b, _ = parses[0]
                base = "kilogram" if (prefix, b) == ("kilo", "gram") else b
            if base is None:
                base = unit_name
            target[base] = target.get(base, 0) + exponent
        return quantity.to("*".join(f"{n}**{e}" for n, e in target.items()))

    _SCI_DEFAULT_PRECISION = 3
    """Default decimal places for scientific notation when `decimals` is None.

    pint's float-based unit conversions can leak precision noise (e.g. 100 mm^2
    becomes 9.999999999999999e-5 m^2 instead of 1e-4 m^2). Using a precision cap
    (`.3e`) rounds it back cleanly without imposing a cap on the natural variable
    form of values that don't go through a unit conversion.
    """

    def _format_quantity_for_substitution(
        quantity: pint.Quantity,
        decimals: int | None,
        *,
        scientific: bool = False,
    ) -> str:
        """Format a pint quantity for inclusion in a substituted LaTeX line.

        decimals=None and not scientific: pint's natural format (Python repr).
        decimals=None and scientific:     `.{_SCI_DEFAULT_PRECISION}e`.
        decimals=N and not scientific:    `.{N+1}f` with trailing-zero trim.
        decimals=N and scientific:        `.{N+1}e`.
        """
        if decimals is None:
            if scientific:
                return f"{quantity:.{_SCI_DEFAULT_PRECISION}e~L}"
            return f"{quantity:~L}"
        n = decimals + 1
        if scientific:
            return f"{quantity:.{n}e~L}"
        formatted = f"{quantity:.{n}f~L}"
        mag_str, sep, unit_str = formatted.partition("\\ ")
        if "." in mag_str:
            mag_str = mag_str.rstrip("0").rstrip(".")
        return f"{mag_str}{sep}{unit_str}"

    def _splice_into_latex(
        rendered_latex: str,
        placeholder_syms: list[sympy.Symbol],
        formatteds: list[str],
        wrappable: list[bool],
    ) -> str:
        """Replace each placeholder in `rendered_latex` with its formatted value.

        When `wrappable[i]` is True and the placeholder is immediately followed
        by `^`, wrap the substitution in `\\left(...\\right)` so the exponent
        binds to the whole quantity, not just the unit.
        """
        for ph, fmt, wrap in zip(placeholder_syms, formatteds, wrappable):
            ph_latex = latex(ph)
            plain = rf"\medspace{fmt}"
            if wrap:
                wrapped = rf"\medspace\left({fmt}\right)"
                rendered_latex = rendered_latex.replace(f"{ph_latex}^", f"{wrapped}^")
            rendered_latex = rendered_latex.replace(ph_latex, plain)
        return rendered_latex

    _VALID_MODES = ("multi_line", "verbose", "one_line")

    class SymbolicEvaluation:
        """A pint Quantity with an attached LaTeX rendering for marimo/Jupyter.

        Returned by `sym_evalf`. Delegates the common Quantity surface
        (magnitude, units, dimensionality, m, m_as, to, to_base_units) to
        `self.quantity`. `_repr_latex_` returns the rendered LaTeX. `.symbol`
        holds the output sympy.Symbol so the result can be plugged back into
        downstream sympy expressions (chained calculations).
        """

        def __init__(
            self,
            quantity: pint.Quantity,
            latex: str,
            symbol: sympy.Symbol,
        ) -> None:
            self.quantity = quantity
            self.latex = latex
            self.symbol = symbol

        @property
        def magnitude(self):
            return self.quantity.magnitude

        @property
        def units(self):
            return self.quantity.units

        @property
        def dimensionality(self):
            return self.quantity.dimensionality

        @property
        def m(self):
            return self.quantity.m

        def m_as(self, unit):
            return self.quantity.m_as(unit)

        def to(self, *args, **kwargs):
            return self.quantity.to(*args, **kwargs)

        def to_base_units(self):
            return self.quantity.to_base_units()

        def _repr_latex_(self) -> str:
            # Always wrap as display math so the default rendering is the larger
            # block form. Inline embeds use `result.latex` directly with `$...$`.
            return f"$$ {self.latex} $$"

        def __repr__(self):
            return f"SymbolicEvaluation({self.quantity!r})"

        def __str__(self):
            return str(self.quantity)

    def sym_evalf(
        expr: sympy.Expr,
        *,
        subs: dict[sympy.Symbol, pint.Quantity] | None = None,
        output_symbol: str | sympy.Symbol,
        output_unit: str | pint.Unit | None = None,
        decimals: int | None = None,
        mode: Literal["multi_line", "verbose", "one_line"] = "multi_line",
        **evalf_kwargs,
    ) -> "SymbolicEvaluation":
        """Numerically evaluate `expr` and produce a LaTeX rendering of the chain.

        Same numeric kernel as `quantity_evalf`; the addition is the LaTeX
        derivation attached to the returned `SymbolicEvaluation`.

        Args:
            expr (sympy.Expr): The sympy expression to evaluate.
            subs (dict[sympy.Symbol, pint.Quantity] | None): Mapping from
                `sympy.Symbol` to `pint.Quantity` (or a scalar for dimensionless
                inputs). Same shape as sympy.evalf's `subs` kwarg. Defaults to
                None (no substitutions).
            output_symbol (str | sympy.Symbol): LaTeX label for the output — a
                string like `r"\\sigma"` or a `sympy.Symbol`. The label appears
                on the left of every line of the rendered chain. Required;
                keyword-only.
            output_unit (str | pint.Unit | None): Target pint unit for the
                result. If `None`, the result is rendered in SI base units.
                Defaults to None.
            decimals (int | None): Number of decimal places for the result and
                substituted lines. `None` uses pint's natural (Python
                `repr(float)`) format. Defaults to None.
            mode (Literal["multi_line", "verbose", "one_line"]): Rendering
                style, defaults to `"multi_line"`:

                - `"multi_line"`: three lines — symbolic, substituted with
                  units, then result.
                - `"verbose"`: four lines — multi_line plus an extra
                  substituted-in-SI-base line in scientific notation.
                - `"one_line"`: a single line —
                  `Symbol = formula = substituted = result`, with just the
                  variable's unit on the right (no prefix-stripped dual).
            **evalf_kwargs: Forwarded to `expr.evalf(...)` via
                `quantity_evalf`. Useful kwargs: `n` (digits of precision),
                `chop`, `strict`.

        Returns:
            SymbolicEvaluation: The computed `pint.Quantity` with the rendered
                LaTeX chain attached. Renders in marimo / Jupyter via
                `_repr_latex_`. Has `.quantity`, `.latex`, and `.symbol` for
                chaining into downstream sympy expressions.

        Raises:
            ValueError: If `mode` is not one of the allowed values.
        """
        if mode not in _VALID_MODES:
            raise ValueError(f"mode must be one of {_VALID_MODES}, got {mode!r}")
        subs = subs or {}

        # Step 1: Symbolic LaTeX (formula with symbols).
        expression_latex = latex(expr)

        # Step 2: Build the substituted LaTeX (formula with numbers).
        # Why placeholders instead of substituting values directly?
        #   - Pint quantities aren\'t sympy values, so subs would drop the units.
        #   - Substituting plain numbers triggers sympy simplification (a+a -> 2a),
        #     which would destroy the structural shape we want to display.
        # So we swap each input symbol for a unique placeholder symbol, then let
        # sympy render the structure, then post-process to splice in our
        # `number + unit` formatting. The trailing "Z" makes substring .replace
        # safe: SymEvalPH0Z is unique even when SymEvalPH10Z exists.
        #
        # Placeholder indices follow the canonical sort order of the *original*
        # input symbols, so sympy.Mul ordering matches between the symbolic and
        # substituted lines.
        input_symbols = list(subs.keys())
        input_quantities = list(subs.values())
        canonical_order = sorted(
            range(len(input_symbols)), key=lambda i: input_symbols[i].sort_key()
        )
        placeholder_syms = [None] * len(input_symbols)
        for canonical_pos, orig_idx in enumerate(canonical_order):
            placeholder_syms[orig_idx] = sympy.Symbol(f"SymEvalPH{canonical_pos}Z")
        sub_map = dict(zip(input_symbols, placeholder_syms))
        rendered = latex(expr.subs(sub_map, simultaneous=True))

        wrappable = [not q.dimensionless for q in input_quantities]
        formatteds_var = [
            _format_quantity_for_substitution(q, decimals, scientific=False)
            for q in input_quantities
        ]
        substituted_latex = _splice_into_latex(
            rendered, placeholder_syms, formatteds_var, wrappable
        )

        # Step 2.5 (verbose only): SI-base substituted line. Each value uses
        # scientific notation when SI-prefix-stripping changed its unit, plain
        # decimal otherwise.
        si_substituted_latex = None
        if mode == "verbose":
            formatteds_si = []
            for q in input_quantities:
                si_q = _strip_si_prefixes(q)
                converted = si_q.units != q.units
                formatteds_si.append(
                    _format_quantity_for_substitution(
                        si_q, decimals, scientific=converted
                    )
                )
            si_substituted_latex = _splice_into_latex(
                rendered, placeholder_syms, formatteds_si, wrappable
            )

        # Step 3: Numerical evaluation. Delegate to quantity_evalf, which forwards
        # the evalf kwargs.
        output_quantity = quantity_evalf(
            expr, subs=subs, output_unit=output_unit, **evalf_kwargs
        )

        # Result line: variable\'s unit, plus prefix-stripped scientific dual
        # when the variable\'s unit carries an SI prefix. With `decimals` set,
        # the dual uses `.{decimals}e`; with `decimals=None` it falls back to
        # `.{_SCI_DEFAULT_PRECISION}e`.
        decimal_fmt = f".{decimals}f" if decimals is not None else ""
        sci_decimals = decimals if decimals is not None else _SCI_DEFAULT_PRECISION
        output_var_unit_latex = f"{output_quantity:{decimal_fmt}~L}"
        no_prefix_quantity = _strip_si_prefixes(output_quantity)
        if no_prefix_quantity.units != output_quantity.units:
            no_prefix_latex = f"{no_prefix_quantity:.{sci_decimals}e~L}"
            output_dual_latex = f"{no_prefix_latex} = {output_var_unit_latex}"
        else:
            output_dual_latex = output_var_unit_latex

        # Coerce output_symbol to a sympy.Symbol for both rendering and chaining.
        if isinstance(output_symbol, sympy.Symbol):
            output_sym = output_symbol
        else:
            output_sym = sympy.Symbol(str(output_symbol))
        sym_latex = latex(output_sym)
        # `full_latex` is the BARE LaTeX (no `$` delimiters). SymbolicEvaluation._repr_latex_
        # adds `$$...$$` for the default display rendering. Callers embedding the
        # math elsewhere wrap explicitly via `result.latex` (`${...}$` for inline,
        # `$${...}$$` for display).
        if mode == "one_line":
            full_latex = (
                f"{sym_latex} = {expression_latex}"
                f" = {substituted_latex}"
                f" = {output_var_unit_latex}"
            )
        else:
            align_lines = [
                rf"{sym_latex} &= {expression_latex} \\",
                rf"&= {substituted_latex} \\",
            ]
            if mode == "verbose":
                align_lines.append(rf"&= {si_substituted_latex} \\")
            align_lines.append(rf"{sym_latex} &= {output_dual_latex}")
            full_latex = (
                "\\begin{align*}\n" + "\n".join(align_lines) + "\n\\end{align*}"
            )

        return SymbolicEvaluation(output_quantity, full_latex, output_sym)

    # Method bindings on sympy.Expr so users can write `expr.sym_evalf(...)`.
    # Bind the functions directly (not via lambdas) so introspection tools
    # — `help`, marimo's 'View live docs', IDE hovers — see the real
    # signature and docstring rather than a generic `lambda(**kw)`.
    sympy.Expr.quantity_evalf = quantity_evalf
    sympy.Expr.sym_evalf = sym_evalf
    return quantity_evalf, sym_evalf


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Lessons Learned

    ### Default precision (no `decimals` kwarg)

    When you don\'t pass `decimals=...`, the variable form on the result line
    uses pint\'s default magnitude format — which is just Python\'s `repr(float)`.
    That means the precision **depends on the value**, not on a fixed default:
    """)
    return


@app.cell
def _():
    return


@app.cell
def _(Quantity):
    # pint's default magnitude format is Python's repr(float) — varies with the value.
    [
        f"{v!r:>16}  ->  {Quantity(v, 'Pa'):~L}"
        for v in (500, 500.0, 1.5, 1.234, 1234567.89, 0.000001)
    ]
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    For the prefix-stripped scientific form on the result line, symeval falls back
    to **3 decimals** when `decimals` is not set — both to give it a defined
    precision and to suppress float-conversion noise (pint computing
    `100 mm² → 9.999...e-5 m²` instead of `1e-4 m²` is a real artifact of float
    unit ratios).
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""

    """)
    return


@app.cell(column=2, hide_code=True)
def _(mo):
    mo.md(r"""
    # `pytest` Tests
    """)
    return


@app.cell
def _(Quantity, quantity_evalf, sympy):
    def test_quantity_evalf_basic():
        """quantity_evalf returns a plain pint.Quantity (not a SymbolicEvaluation)."""
        F, A = sympy.symbols("F A")
        q = quantity_evalf(
            F / A,
            subs={F: Quantity(50, "kN"), A: Quantity(100, "mm^2")},
            output_unit="MPa",
        )
        assert isinstance(q, type(Quantity(1, "Pa")))
        assert q.units == Quantity(1, "MPa").units
        assert abs(q.magnitude - 500) < 0.001

    def test_quantity_evalf_method_on_expr():
        """The monkey-patched .quantity_evalf(...) method works the same way."""
        F, A = sympy.symbols("F A")
        q = (F / A).quantity_evalf(
            subs={F: Quantity(50, "kN"), A: Quantity(100, "mm^2")},
            output_unit="MPa",
        )
        assert abs(q.magnitude - 500) < 0.001

    def test_quantity_evalf_no_output_unit():
        """Without output_unit, the result lands in fully-reduced SI base units."""
        F, A = sympy.symbols("F A")
        q = quantity_evalf(
            F / A, subs={F: Quantity(50, "kN"), A: Quantity(100, "mm^2")}
        )
        # Dimensionality matches a stress (Pa), but the units form is the
        # fully-reduced kg/(m·s²) rather than the derived Pa.
        assert q.dimensionality == Quantity(1, "Pa").dimensionality
        assert abs(q.magnitude - 5e8) < 1

    def test_quantity_evalf_no_subs():
        """With subs=None (no substitutions), a constant sympy expression evaluates fine."""
        q = quantity_evalf(sympy.pi**2)
        assert abs(float(q.magnitude) - 9.8696) < 0.001

    def test_quantity_evalf_forwards_evalf_kwargs():
        """**evalf_kwargs are passed through to expr.evalf — passing `n` shouldn\'t crash."""
        F, A = sympy.symbols("F A")
        q = quantity_evalf(
            F / A,
            subs={F: Quantity(50, "kN"), A: Quantity(100, "mm^2")},
            output_unit="MPa",
            n=20,
        )
        assert abs(q.magnitude - 500) < 0.001

    return


@app.cell
def _(Quantity, sym_evalf, sympy):
    def test_sym_evalf_basic():
        """Test the Euler buckling example using the free function."""
        k, E, L, r_y = sympy.symbols("k E L r_y")
        expr = (sympy.pi**2 * E) / ((k * L / r_y) ** 2)
        result = sym_evalf(
            expr,
            subs={
                k: Quantity(1, ""),
                E: Quantity(200, "GPa"),
                L: Quantity(6.5, "m"),
                r_y: Quantity(76.1, "mm"),
            },
            output_symbol="F_e",
            output_unit="GPa",
            decimals=3,
        )
        assert result.quantity.units == Quantity(1, "GPa").units
        assert abs(result.quantity.magnitude - 0.271) < 0.001
        assert "F_{e}" in result._repr_latex_()
        assert "\\begin{align*}" in result._repr_latex_()

    def test_sym_evalf_method_on_expr():
        """The monkey-patched `expr.sym_evalf(...)` method works the same way."""
        k, E, L, r_y = sympy.symbols("k E L r_y")
        expr = (sympy.pi**2 * E) / ((k * L / r_y) ** 2)
        result = expr.sym_evalf(
            subs={
                k: Quantity(1, ""),
                E: Quantity(200, "GPa"),
                L: Quantity(6.5, "m"),
                r_y: Quantity(76.1, "mm"),
            },
            output_symbol="F_e",
            output_unit="GPa",
            decimals=3,
        )
        assert abs(result.quantity.magnitude - 0.271) < 0.001

    def test_sym_evalf_renders_three_step_latex():
        """SymbolicEvaluation._repr_latex_ shows the three-step align block."""
        x, y = sympy.symbols("x y")
        expr = x**2 + y**2
        result = sym_evalf(
            expr,
            subs={x: Quantity(3, ""), y: Quantity(4, "")},
            output_symbol="z",
        )
        rendered = result._repr_latex_()
        assert "\\begin{align*}" in rendered
        assert "$$" in rendered

    def test_sym_evalf_no_output_unit():
        """Without `output_unit`, the result lands in SI base units."""
        x, y = sympy.symbols("x y")
        expr = x**2 + y**2
        result = sym_evalf(
            expr, subs={x: Quantity(3, ""), y: Quantity(4, "")}, output_symbol="z"
        )
        assert abs(result.quantity.magnitude - 25) < 0.001

    def test_sym_evalf_simple_multiplication():
        """A * f_y example: stress * area = force."""
        A_sym = sympy.Symbol("A")
        f_y = sympy.Symbol("f_y")
        expr = A_sym * f_y
        result = sym_evalf(
            expr,
            subs={A_sym: Quantity(500, "mm^2"), f_y: Quantity(355, "MPa")},
            output_symbol="F",
            output_unit="kN",
            decimals=1,
        )
        assert abs(result.quantity.magnitude - 177.5) < 0.1

    def test_sym_evalf_no_symbol_collision():
        """Symbols like 'r' must not collide with 'r_y' during placeholder substitution."""
        r = sympy.Symbol("r")
        r_y = sympy.Symbol("r_y")
        expr = r + r_y
        result = sym_evalf(
            expr,
            subs={r: Quantity(2, "m"), r_y: Quantity(3, "m")},
            output_symbol="F",
            output_unit="m",
            decimals=1,
        )
        assert abs(result.quantity.magnitude - 5.0) < 0.1
        rendered = result._repr_latex_()
        assert "SymEvalPH" not in rendered
        assert "r_{y}" in rendered

    def test_sym_evalf_kg_unit_not_stripped():
        """kg is the SI base unit for mass; sym_evalf should not strip it to g."""
        m_in = sympy.Symbol("m_in")
        result = sym_evalf(
            m_in,
            subs={m_in: Quantity(2, "kg")},
            output_symbol="m_out",
            output_unit="kg",
            decimals=2,
        )
        assert result.quantity == Quantity(2, "kg")
        rendered = result._repr_latex_()
        assert r"\mathrm{kg}" in rendered
        assert r"\mathrm{g}" not in rendered

    return


@app.cell
def _(Quantity, sym_evalf, sympy):
    def stress_calc(mode=None):
        """Helper: σ = F/A → MPa, returns the SymbolicEvaluation."""
        F = sympy.Symbol("F")
        A = sympy.Symbol("A")
        kwargs = {} if mode is None else {"mode": mode}
        return sym_evalf(
            F / A,
            subs={F: Quantity(50, "kN"), A: Quantity(100, "mm^2")},
            output_symbol=r"\sigma",
            output_unit="MPa",
            decimals=2,
            **kwargs,
        )

    return (stress_calc,)


@app.cell
def _(Quantity, stress_calc, sym_evalf, sympy):
    def test_sym_evalf_mode_default_is_multi_line():
        """Default mode matches mode='multi_line' explicitly."""
        assert stress_calc().latex == stress_calc(mode="multi_line").latex

    def test_sym_evalf_mode_verbose():
        """Verbose adds an extra SI-base substituted line."""
        multi = stress_calc(mode="multi_line").latex
        verbose = stress_calc(mode="verbose").latex
        assert verbose.count(r"\\") == multi.count(r"\\") + 1
        assert r"5.000\times 10^{4}" in verbose
        assert r"\mathrm{N}" in verbose
        assert r"500.00\ \mathrm{MPa}" in verbose

    def test_sym_evalf_mode_one_line():
        """One-line: no align block, includes substituted intermediate, no prefix-strip dual."""
        one = stress_calc(mode="one_line").latex
        assert r"\begin{align" not in one
        assert r"50\ \mathrm{kN}" in one
        assert r"100\ \mathrm{mm}" in one
        assert r"500.00\ \mathrm{MPa}" in one
        assert r"\mathrm{Pa} = " not in one

    def test_sym_evalf_mode_invalid_raises():
        """An unknown mode raises ValueError listing the allowed values."""
        F = sympy.Symbol("F")
        A = sympy.Symbol("A")
        try:
            sym_evalf(
                F / A,
                subs={F: Quantity(50, "kN"), A: Quantity(100, "mm^2")},
                output_symbol=r"\sigma",
                output_unit="MPa",
                mode="bogus",
            )
        except ValueError as e:
            assert "multi_line" in str(e)
            assert "verbose" in str(e)
            assert "one_line" in str(e)
        else:
            raise AssertionError("Expected ValueError for invalid mode")

    return


if __name__ == "__main__":
    app.run()
