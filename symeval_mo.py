# /// script
# requires-python = ">=3.12"
# dependencies = [
#     "marimo",
#     "pint==0.25.3",
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


@app.cell
def _():
    import marimo as mo

    return (mo,)


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Example: axial stress under load

    The axial stress $\sigma$ in a bar of cross-sectional area $A$ under axial
    force $F$:

    $$\sigma = \frac{F}{A}$$

    Below: the same calculation rendered in each of symeval's three modes —
    `multi_line` (default), `verbose`, and `one_line`.
    """)
    return


@app.cell
def _(Variable):
    from sympy import Symbol, symbols

    sigma_var = Variable(r"\sigma", name="Axial stress", unit="MPa")
    sigma_expr = Symbol("F") / Symbol("A")
    f = Variable("F", name="Axial force", value=50, unit="kN")
    a = Variable("A", name="Cross-sectional area", value=100.000, unit="mm^2")

    sigma_expr.symeval(
        sigma_var,
        inputs=[f, a],
    )
    return a, f, sigma_expr, sigma_var


@app.cell
def _(a, f, sigma_expr, sigma_var):
    # You can specify the number of decimal places of your result, and the render mode:
    # verbose: adds an extra line showing all values converted to SI base units.
    sigma_expr.symeval(sigma_var, inputs=[f, a], decimals=2, mode="verbose")
    return


@app.cell
def _(a, f, sigma_expr, sigma_var):
    # one_line: collapse the derivation onto a single line.
    sigma_expr.symeval(sigma_var, inputs=[f, a], mode="one_line")
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
def _(mo):
    # Variable specs: single source of truth for metadata + UI defaults.
    input_specs = [
        {"section": "Loads"},
        {"key": "compressive_force", "latex": "C_f", "name": "Compressive force", "unit": "kN", "default": 680},
        {"section": "Member geometry"},
        {"key": "beam_length", "latex": "L", "name": "Beam length", "unit": "m", "default": 6.5, "step": 0.1},
        {"key": "effective_length_factor", "latex": "k", "name": "Effective length factor", "default": 1, "step": 0.1},
        {"section": "Material properties"},
        {"key": "elastic_modulus", "latex": "E", "name": "Elastic modulus", "unit": "GPa", "default": 200},
        {"key": "yield_strength", "latex": "F_y", "name": "Yield strength", "unit": "MPa", "default": 400},
        {"key": "n", "latex": "n", "name": "Strain-hardening exponent", "default": 1.34, "step": 0.01},
        {"key": "strength_reduction_factor", "latex": r"\phi_s", "name": "Strength reduction factor", "default": 0.85, "step": 0.05},
        {"section": "Member section properties"},
        {"key": "cross_sectional_area", "latex": "A", "name": "Cross-sectional area", "unit": "mm^2", "default": 10_300},
        {"key": "radius_gyration", "latex": "r_y", "name": "Radius of gyration about the y-axis", "unit": "mm", "default": 76.1, "step": 0.1},
    ]

    # mo.ui.dictionary makes the whole bundle a reactive UIElement; a plain dict
    # would hide the input elements from marimo's static analysis and break reactivity.
    inputs = mo.ui.dictionary({
        s["key"]: mo.ui.number(value=s["default"], step=s.get("step", 1))
        for s in input_specs if "key" in s
    })

    return input_specs, inputs


@app.cell(hide_code=True)
def _(input_specs, inputs, mo):
    def _spec_row(s):
        if "section" in s:
            return f"| **{s['section']}** |  |  |  |  |"
        unit = f"${s['unit']}$" if s.get("unit") else ""
        return f"| {s['name']} | ${s['latex']}$ | = | {inputs[s['key']]} | {unit} |"

    mo.md(
        "|     |     |     |     |     |\n"
        "|--------------|--------|---|-----|---|\n"
        + "\n".join(_spec_row(s) for s in input_specs)
    )

    return


@app.cell(hide_code=True)
def _(Variable, input_specs, inputs):
    _vars = {
        s["key"]: Variable(
            latex=s["latex"],
            name=s["name"],
            unit=s.get("unit"),
            value=inputs.value[s["key"]],
        )
        for s in input_specs if "key" in s
    }

    compressive_force = _vars["compressive_force"]
    beam_length = _vars["beam_length"]
    effective_length_factor = _vars["effective_length_factor"]
    elastic_modulus = _vars["elastic_modulus"]
    yield_strength = _vars["yield_strength"]
    n = _vars["n"]
    strength_reduction_factor = _vars["strength_reduction_factor"]
    cross_sectional_area = _vars["cross_sectional_area"]
    radius_gyration = _vars["radius_gyration"]

    return (
        beam_length,
        compressive_force,
        cross_sectional_area,
        effective_length_factor,
        elastic_modulus,
        n,
        radius_gyration,
        strength_reduction_factor,
        yield_strength,
    )


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ### Euler Buckling Stress
    """)
    return


@app.cell(hide_code=True)
def _(
    Variable,
    beam_length,
    effective_length_factor,
    elastic_modulus,
    radius_gyration,
    sympy,
):
    euler_buckling_expr = (sympy.pi**2 * elastic_modulus.symbol) / (
        (
            beam_length.symbol
            * effective_length_factor.symbol
            / radius_gyration.symbol
        )
        ** 2
    )
    euler_buckling_stress = euler_buckling_expr.symeval(
        output_variable=Variable("F_e", name="Euler buckling stress", unit="GPa"),
        inputs=[
            effective_length_factor,
            elastic_modulus,
            beam_length,
            radius_gyration,
        ],
        decimals=3,
    )
    euler_buckling_stress
    return (euler_buckling_stress,)


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ### $\lambda$ Factor
    """)
    return


@app.cell(hide_code=True)
def _(Variable, euler_buckling_stress, n, sympy, yield_strength):
    lambda_factor_expr = (sympy.sqrt(yield_strength.symbol / euler_buckling_stress.symbol)) ** (
        2 * n.symbol
    )
    lambda_factor = lambda_factor_expr.symeval(
        output_variable=Variable(r"\lambda", name=r"\lambda factor", unit=None),
        inputs=[yield_strength, euler_buckling_stress, n],
        decimals=3,
    )
    lambda_factor
    return (lambda_factor,)


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ### Axial Resistance
    """)
    return


@app.cell(hide_code=True)
def _(
    Variable,
    cross_sectional_area,
    lambda_factor,
    n,
    strength_reduction_factor,
    yield_strength,
):
    axial_resistance_expr = (
        strength_reduction_factor.symbol
        * cross_sectional_area.symbol
        * yield_strength.symbol
    ) / ((1 + lambda_factor.symbol) ** (1 / n.symbol))
    axial_resistance = axial_resistance_expr.symeval(
        output_variable=Variable("C_r", name="Axial resistance", unit="MN"),
        inputs=[
            strength_reduction_factor,
            cross_sectional_area,
            yield_strength,
            lambda_factor,
            n,
        ],
        decimals=3,
    )
    axial_resistance
    return (axial_resistance,)


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ### Demand Capacity Ratio
    """)
    return


@app.cell(hide_code=True)
def _(Variable, axial_resistance, compressive_force):
    dcr_expr = compressive_force.symbol / axial_resistance.symbol
    dcr = dcr_expr.symeval(
        output_variable=Variable("DCR", name="Demand capacity ratio", unit=None),
        inputs=[compressive_force, axial_resistance],
        decimals=3,
    )
    dcr
    return


@app.cell(column=1, hide_code=True)
def _(mo):
    mo.md(r"""
    # Implementation
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    Cells marked with `## EXPORT` are extracted into a Python package via
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

    return Literal, dataclass, field, latex, pint, sympy


@app.cell
def _(pint):
    ## EXPORT

    # Default unit registry with sensible defaults for engineering calculations
    ureg = pint.UnitRegistry(auto_reduce_dimensions=True)
    ureg.formatter.default_format = "~L"
    Q_ = ureg.Quantity
    return Q_, ureg


@app.cell
def _(Literal, Q_, dataclass, field, latex, sympy, ureg):
    ## EXPORT


    @dataclass
    class Variable:
        """A variable with a sympy symbol, pint quantity, and metadata.

        Args:
            latex: LaTeX symbol string (e.g. "F_e", r"\\phi_s"). Becomes both
                the sympy Symbol and the LaTeX representation.
            name: Human-readable description (e.g. "Euler buckling stress").
            value: Numerical value. None for output-only variables.
            unit: Pint unit string (e.g. "GPa", "mm^2"). None for dimensionless.
            min: Minimum realistic value (for slider bounds).
            max: Maximum realistic value (for slider bounds).
            examples: Named example values (e.g. {"short span": 3, "long span": 12}).
        """

        latex: str
        name: str
        unit: str | None = None
        value: float | None = None
        min: float | None = None
        max: float | None = None
        examples: dict[str, float] | None = field(default=None, repr=False)

        def __post_init__(self):
            self._sympy_symbol = sympy.Symbol(self.latex)
            self._eval_latex: str | None = None

            if self.value is not None:
                if self.unit:
                    self.quantity = Q_(self.value, self.unit)
                else:
                    self.quantity = Q_(self.value, "")
            else:
                self.quantity = None

        @property
        def symbol(self) -> sympy.Symbol:
            """The sympy Symbol for use in expressions."""
            return self._sympy_symbol

        def _pint_to_base_magnitude(self) -> float:
            """Convert quantity to base SI units and return the magnitude."""
            if self.quantity is None:
                raise ValueError(f"Variable '{self.name}' has no value assigned.")
            if self.quantity.dimensionality == {}:
                return self.quantity.magnitude
            return self.quantity.to_base_units().magnitude

        def _pint_to_sympy_base(self) -> sympy.Expr:
            """Convert pint quantity to a sympy expression in base SI units."""
            if self.quantity is None:
                raise ValueError(f"Variable '{self.name}' has no value assigned.")
            if self.quantity.dimensionality == {}:
                return self.quantity.magnitude
            base = self.quantity.to_base_units()
            sympy_units = sympy.sympify(f"{base.units:~D}")
            return base.magnitude * sympy_units

        def _repr_latex_(self) -> str:
            """LaTeX representation for marimo/Jupyter rendering."""
            if self._eval_latex is not None:
                return self._eval_latex
            if self.quantity is not None:
                return f"${self.latex} = {self.quantity:~L}$"
            return f"${self.latex}$"

        def __str__(self) -> str:
            if self.quantity is not None:
                return f"{self.name}: {self.latex} = {self.quantity:~#P}"
            return f"{self.name}: {self.latex}"


    def _strip_si_prefixes(quantity):
        """Convert a quantity to its SI-prefix-free equivalent (kN -> N, MPa -> Pa, mm -> m).

        `kg` is left as-is because it is itself the SI base unit for mass — even
        though pint internally represents it as kilo*gram.
        """
        if quantity.dimensionless:
            return quantity
        target = {}
        for unit_name, exponent in dict(quantity.units._units).items():
            parses = ureg.parse_unit_name(unit_name)
            # Prefer an unprefixed parse (e.g. 'Pa' has both ('', 'pascal', '') and ('peta', 'year', '')).
            base = next((b for prefix, b, _ in parses if prefix == ""), None)
            if base is None and parses:
                # All parses are prefixed (e.g. 'kN' -> ('kilo', 'newton', '')).
                prefix, b, _ = parses[0]
                base = "kilogram" if (prefix, b) == ("kilo", "gram") else b
            if base is None:
                base = unit_name
            target[base] = target.get(base, 0) + exponent
        return quantity.to("*".join(f"{n}**{e}" for n, e in target.items()))


    _SCI_DEFAULT_PRECISION = 3
    """Default decimal places for scientific notation when `decimals` is None.

    pint\'s float-based unit conversions can leak precision noise (e.g. 100 mm^2
    becomes 9.999999999999999e-5 m^2 instead of 1e-4 m^2). Using a precision cap
    (`.3e`) rounds it back cleanly without imposing a cap on the natural variable
    form of values that don\'t go through a unit conversion.
    """


    def _format_quantity_for_substitution(quantity, decimals, *, scientific=False):
        """Format a pint quantity for inclusion in a substituted LaTeX line.

        decimals=None and not scientific: pint\'s natural format (Python repr).
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


    def _splice_into_latex(rendered_latex, placeholder_syms, formatteds, wrappable):
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


    def symeval(
        expr: sympy.Expr,
        output_variable: Variable,
        inputs: list[Variable],
        decimals: int | None = None,
        mode: Literal["multi_line", "verbose", "one_line"] = "multi_line",
    ) -> Variable:
        """Evaluate a sympy expression with pint units, attaching a LaTeX rendering.

        The output_variable is mutated in place: its quantity is set to the
        computed value, and `_eval_latex` is attached so rendering the variable
        in marimo/Jupyter shows the derivation.

        Args:
            expr: The sympy expression to evaluate.
            output_variable: Variable for the output. Its unit (if set) is the
                target output unit; its symbol is used for labeling.
            inputs: List of Variables with values to substitute.
            decimals: Number of decimal places for the output. None uses pint
                defaults throughout.
            mode: Rendering style.
                - "multi_line" (default): symbolic, substituted, result.
                - "verbose": multi_line plus an extra substituted-in-SI-base line
                  (scientific where conversion happened, decimal otherwise).
                - "one_line": `Symbol = expression = result` on one line, using
                  just the variable's unit (no prefix-stripped dual).

        Returns:
            The output_variable, mutated in place.
        """
        if mode not in _VALID_MODES:
            raise ValueError(
                f"mode must be one of {_VALID_MODES}, got {mode!r}"
            )

        # Step 1: Symbolic LaTeX (formula with symbols).
        expression_latex = latex(expr)

        # Step 2: Build the substituted LaTeX (formula with numbers).
        # Why placeholders instead of substituting values directly?
        #   - Pint quantities aren\'t sympy values, so subs would drop the units.
        #   - Substituting plain numbers triggers sympy simplification (a+a -> 2a),
        #     which would destroy the structural shape we want to display.
        # So we swap each input symbol for a unique placeholder symbol, and then
        # let sympy render the structure (fracs, sqrts, parens, ...), then
        # post-process the rendered LaTeX to splice in our `number + unit`
        # formatting. The trailing "Z" makes substring .replace safe: SymEvalPH0Z
        # is unique even when SymEvalPH10Z exists.
        #
        # Placeholder indices follow the canonical sort order of the *original*
        # input symbols, so sympy.Mul ordering matches between the symbolic and
        # substituted lines.
        canonical_order = sorted(
            range(len(inputs)), key=lambda i: inputs[i].symbol.sort_key()
        )
        placeholder_syms = [None] * len(inputs)
        for canonical_pos, orig_idx in enumerate(canonical_order):
            placeholder_syms[orig_idx] = sympy.Symbol(f"SymEvalPH{canonical_pos}Z")
        sub_map = dict(zip([v.symbol for v in inputs], placeholder_syms))
        rendered = latex(expr.subs(sub_map, simultaneous=True))

        wrappable = [not v.quantity.dimensionless for v in inputs]
        formatteds_var = [
            _format_quantity_for_substitution(v.quantity, decimals, scientific=False)
            for v in inputs
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
            for v in inputs:
                si_q = _strip_si_prefixes(v.quantity)
                converted = si_q.units != v.quantity.units
                formatteds_si.append(
                    _format_quantity_for_substitution(si_q, decimals, scientific=converted)
                )
            si_substituted_latex = _splice_into_latex(
                rendered, placeholder_syms, formatteds_si, wrappable
            )

        # Step 3: Numerically evaluate. Pass substitutions via evalf\'s `subs`
        # kwarg (arbitrary-precision substitution) — see
        # https://docs.sympy.org/latest/modules/core.html#module-sympy.core.evalf
        base_unit_inputs = {var.symbol: var._pint_to_sympy_base() for var in inputs}
        result_value = expr.evalf(subs=base_unit_inputs)
        output_quantity = ureg(f"{result_value}")
        if output_variable.unit:
            output_quantity = output_quantity.to(output_variable.unit)

        # Result line: variable\'s unit, plus prefix-stripped scientific dual
        # when the variable\'s unit carries an SI prefix. With `decimals` set,
        # the dual uses `.{decimals}e`; with `decimals=None` it falls back to
        # `.{_SCI_DEFAULT_PRECISION}e` — bare `e` is Python\'s default (6 decimals)
        # which would jar against the variable form\'s natural precision.
        decimal_fmt = f".{decimals}f" if decimals is not None else ""
        sci_decimals = decimals if decimals is not None else _SCI_DEFAULT_PRECISION
        output_var_unit_latex = f"{output_quantity:{decimal_fmt}~L}"
        no_prefix_quantity = _strip_si_prefixes(output_quantity)
        if no_prefix_quantity.units != output_quantity.units:
            no_prefix_latex = f"{no_prefix_quantity:.{sci_decimals}e~L}"
            output_dual_latex = f"{no_prefix_latex} = {output_var_unit_latex}"
        else:
            output_dual_latex = output_var_unit_latex

        # Assemble the final LaTeX based on mode.
        sym_latex = latex(output_variable.symbol)
        if mode == "one_line":
            # `Symbol = formula = substituted = result` on a single line, using
            # just the variable\'s unit on the right (no prefix-stripped dual).
            full_latex = (
                f"$$\n{sym_latex} = {expression_latex}"
                f" = {substituted_latex}"
                f" = {output_var_unit_latex}\n$$"
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
                "$$\n\\begin{align*}\n"
                + "\n".join(align_lines)
                + "\n\\end{align*}\n$$"
            )

        output_variable.quantity = output_quantity
        output_variable._eval_latex = full_latex
        return output_variable


    # Monkey-patch .symeval() onto sympy expressions
    def _symeval_method(self, output_variable, inputs, decimals=None, mode="multi_line"):
        """Convenience method patched onto sympy.Expr. See symeval() for docs."""
        return symeval(
            self,
            output_variable=output_variable,
            inputs=inputs,
            decimals=decimals,
            mode=mode,
        )


    sympy.Expr.symeval = _symeval_method

    return Variable, symeval


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
def _(Q_):
    # pint's default magnitude format is Python's repr(float) — varies with the value.
    [
        f"{v!r:>16}  ->  {Q_(v, 'Pa'):~L}"
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
    # Tests
    """)
    return


@app.cell
def _(Q_, Variable, a, f, symeval, sympy):
    ## Put pytests here.

    def test_variable_with_unit():
        v = Variable("F_y", name="Yield strength", value=400, unit="MPa")
        assert v.symbol == sympy.Symbol("F_y")
        assert v.quantity == Q_(400, "MPa")
        assert v.name == "Yield strength"


    def test_variable_dimensionless():
        v = Variable("k", name="Effective length factor", value=1)
        assert v.quantity == Q_(1, "")
        assert v._pint_to_base_magnitude() == 1


    def test_variable_no_value():
        v = Variable("F_e", name="Euler buckling stress")
        assert v.quantity is None
        assert v.symbol == sympy.Symbol("F_e")


    def test_variable_with_bounds():
        v = Variable("L", name="Beam length", value=6.5, unit="m", min=1, max=20)
        assert v.min == 1
        assert v.max == 20


    def test_variable_with_examples():
        v = Variable(
            "L",
            name="Beam length",
            value=6.5,
            unit="m",
            examples={"short": 3, "typical": 6.5, "long": 12},
        )
        assert v.examples["short"] == 3


    def test_variable_repr_latex():
        v = Variable("F_y", name="Yield strength", value=400, unit="MPa")
        result = v._repr_latex_()
        assert "F_y" in result
        assert "$" in result


    def test_variable_output_only_repr_latex():
        v = Variable("F_e", name="Euler buckling stress")
        result = v._repr_latex_()
        assert "F_e" in result


    def test_basic_symeval():
        """Test the Euler buckling example from the original notebook."""
        F_e = Variable("F_e", name="Euler buckling stress", unit="GPa")
        k = Variable("k", name="Effective length factor", value=1)
        E = Variable("E", name="Elastic modulus", value=200, unit="GPa")
        L = Variable("L", name="Beam length", value=6.5, unit="m")
        r_y = Variable("r_y", name="Radius of gyration", value=76.1, unit="mm")

        expr = (sympy.pi**2 * E.symbol) / ((k.symbol * L.symbol / r_y.symbol) ** 2)

        result = symeval(
            expr, output_variable=F_e, inputs=[k, E, L, r_y], decimals=3
        )

        assert result is F_e
        assert F_e.quantity.units == Q_(1, "GPa").units
        assert abs(F_e.quantity.magnitude - 0.271) < 0.001
        assert "F_{e}" in F_e._repr_latex_()
        assert "\\begin{align*}" in F_e._repr_latex_()


    def test_symeval_method_on_expr():
        """Test the monkey-patched .symeval() method."""
        F_e = Variable("F_e", name="Euler buckling stress", unit="GPa")
        k = Variable("k", name="Effective length factor", value=1)
        E = Variable("E", name="Elastic modulus", value=200, unit="GPa")
        L = Variable("L", name="Beam length", value=6.5, unit="m")
        r_y = Variable("r_y", name="Radius of gyration", value=76.1, unit="mm")

        expr = (sympy.pi**2 * E.symbol) / ((k.symbol * L.symbol / r_y.symbol) ** 2)

        result = expr.symeval(
            output_variable=F_e, inputs=[k, E, L, r_y], decimals=3
        )
        assert result is F_e
        assert abs(F_e.quantity.magnitude - 0.271) < 0.001


    def test_symeval_renders_three_step_latex():
        """Output variable's _repr_latex_ shows the three-step chain after symeval."""
        x = Variable("x", name="x", value=3)
        y = Variable("y", name="y", value=4)
        z = Variable("z", name="result", unit=None)
        expr = x.symbol**2 + y.symbol**2
        symeval(expr, output_variable=z, inputs=[x, y])
        rendered = z._repr_latex_()
        assert "\\begin{align*}" in rendered
        assert "$$" in rendered


    def test_symeval_no_unit():
        """Test symeval without specifying output unit."""
        x = Variable("x", name="x", value=3)
        y = Variable("y", name="y", value=4)
        z = Variable("z", name="result")
        expr = x.symbol**2 + y.symbol**2
        result = symeval(expr, output_variable=z, inputs=[x, y])
        assert abs(result.quantity.magnitude - 25) < 0.001


    def test_symeval_simple_multiplication():
        """Test A * f_y example from design doc."""
        F = Variable("F", name="Force", unit="kN")
        A = Variable("A", name="Cross-sectional area", value=500, unit="mm^2")
        f_y = Variable("f_y", name="Yield strength", value=355, unit="MPa")

        expr = A.symbol * f_y.symbol
        result = symeval(expr, output_variable=F, inputs=[A, f_y], decimals=1)
        assert abs(result.quantity.magnitude - 177.5) < 0.1


    def test_no_symbol_collision():
        """Symbols like 'r' must not collide with 'r_y' during LaTeX substitution.

        Originally caught a bug where string-level placeholder replacement chewed
        up variable names that appeared as substrings of the placeholder word
        (e.g. 'E', 'L', 'R' inside '__PLACEHOLDER__'). The current sympy-level
        substitution is symbol-aware, so this verifies no such substring leak.
        """
        F = Variable("F", name="Force", unit="m")
        r = Variable("r", name="Radius", value=2, unit="m")
        r_y = Variable("r_y", name="Radius y", value=3, unit="m")

        expr = r.symbol + r_y.symbol
        result = symeval(expr, output_variable=F, inputs=[r, r_y], decimals=1)
        assert abs(result.quantity.magnitude - 5.0) < 0.1
        rendered = result._repr_latex_()
        assert "SymEvalPHZ" not in rendered
        assert "r_{y}" in rendered


    def test_kg_unit_not_stripped():
        """`kg` is conventionally the SI base for mass; symeval should not strip it to `g`.

        Contrast with `kN`, where the result line shows both `<value> N = <value> kN`.
        """
        m_in = Variable("m_in", name="Input mass", value=2, unit="kg")
        m_out = Variable("m_out", name="Output mass", unit="kg")
        m_in.symbol.symeval(m_out, inputs=[m_in], decimals=2)
        assert m_out.quantity == Q_(2, "kg")
        eval_latex = m_out._eval_latex
        assert r"\mathrm{kg}" in eval_latex
        # Would only appear if kg was stripped to gram — it shouldn't.
        assert r"\mathrm{g}" not in eval_latex


    def _stress_calc(mode=None):
        """Helper for the mode tests: σ = F/A in N/mm^2, returns the output Variable."""
        F = Variable("F", name="Axial force", value=50, unit="kN")
        A = Variable("A", name="Cross-sectional area", value=100, unit="mm^2")
        out = Variable(r"\sigma", name="Axial stress", unit="MPa")
        kwargs = {} if mode is None else {"mode": mode}
        (F.symbol / A.symbol).symeval(out, inputs=[f, a], decimals=2, **kwargs)
        return out


    def test_symeval_mode_default_is_multi_line():
        """Calling without `mode` produces the same _eval_latex as mode='multi_line'."""
        default = _stress_calc()._eval_latex
        explicit = _stress_calc(mode="multi_line")._eval_latex
        assert default == explicit


    def test_symeval_mode_verbose():
        """Verbose mode adds an extra SI-base substituted line."""
        multi = _stress_calc(mode="multi_line")._eval_latex
        verbose = _stress_calc(mode="verbose")._eval_latex
        # Verbose has exactly one more align line break (\\) than multi_line.
        assert verbose.count(r"\\") == multi.count(r"\\") + 1
        # The SI-converted scientific value 5e4 N appears on the new line.
        assert r"5.000\times 10^{4}" in verbose
        assert r"\mathrm{N}" in verbose
        # Result line still has the prefix-strip dual `... Pa = 500.00 MPa`.
        assert r"500.00\ \mathrm{MPa}" in verbose


    def test_symeval_mode_one_line():
        """One-line: no align block, includes substituted intermediate, no prefix-strip dual."""
        one = _stress_calc(mode="one_line")._eval_latex
        assert r"\begin{align" not in one
        # Substituted intermediate is present.
        assert r"50\ \mathrm{kN}" in one
        assert r"100\ \mathrm{mm}" in one
        # Result uses just the variable's unit, no prefix-stripped dual.
        assert r"500.00\ \mathrm{MPa}" in one
        assert r"\mathrm{Pa} = " not in one


    def test_symeval_mode_invalid_raises():
        """An unknown `mode` raises ValueError, mentioning the allowed values."""
        F = Variable("F", name="Axial force", value=50, unit="kN")
        A = Variable("A", name="Cross-sectional area", value=100, unit="mm^2")
        out = Variable(r"\sigma", name="Axial stress", unit="MPa")
        try:
            (F.symbol / A.symbol).symeval(out, inputs=[f, a], decimals=2, mode="bogus")
        except ValueError as e:
            assert "multi_line" in str(e)
            assert "verbose" in str(e)
            assert "one_line" in str(e)
        else:
            raise AssertionError("Expected ValueError for invalid mode")


    return


if __name__ == "__main__":
    app.run()
