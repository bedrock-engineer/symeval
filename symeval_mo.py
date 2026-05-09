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
        {"key": "effective_length_factor", "latex": "k", "name": "Effective length factor", "default": 1},
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
            effective_length_factor.symbol
            * beam_length.symbol
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

    import pint
    import sympy
    from sympy import latex

    return dataclass, field, latex, pint, sympy, textwrap


@app.cell
def _(pint):
    ## EXPORT

    # Default unit registry with sensible defaults for engineering calculations
    ureg = pint.UnitRegistry(auto_reduce_dimensions=True)
    ureg.formatter.default_format = "~L"
    Q_ = ureg.Quantity
    return Q_, ureg


@app.cell
def _(Q_, dataclass, field, latex, sympy, textwrap, ureg):
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

        # TODO: add an optional description

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


    def symeval(
        expr: sympy.Expr,
        output_variable: Variable,
        inputs: list[Variable],
        decimals: int | None = None,
    ) -> Variable:
        """Evaluate a sympy expression with pint units, producing a three-step LaTeX rendering.

        The output_variable is mutated in place: its quantity is set to the computed
        value, and a three-step LaTeX rendering is attached so that rendering the
        variable in marimo/Jupyter shows the full derivation.

        Args:
            expr: The sympy expression to evaluate.
            output_variable: Variable for the output. Its unit (if set) is the target
                output unit; its symbol is used for labeling.
            inputs: List of Variables with values to substitute.
            decimals: Number of decimal places for the output. If None, uses default.

        Returns:
            The output_variable, mutated in place with the computed quantity and
            three-step LaTeX attached.
        """
        # Step 1: Build the symbolic LaTeX (formula with symbols)
        expression_latex = latex(expr)

        # Step 2: Build the substituted LaTeX (formula with numbers).
        # Substitute at the sympy level (symbol-aware), then render once, then
        # replace each placeholder's rendered LaTeX with the value's LaTeX.
        # Substring-safe: the trailing "Z" prevents SYMEVALPH0 matching inside SYMEVALPH10.
        placeholder_syms = [
            sympy.Symbol(f"SYMEVALPH{i}Z") for i in range(len(inputs))
        ]
        sub_map = dict(zip([v.symbol for v in inputs], placeholder_syms))
        substituted_latex = latex(expr.subs(sub_map, simultaneous=True))
        for ph_sym, var in zip(placeholder_syms, inputs):
            substituted_latex = substituted_latex.replace(
                latex(ph_sym), rf"\medspace{var.quantity:~L}"
            )

        # Step 3: Numerically evaluate
        base_unit_inputs = {
            var.symbol: var._pint_to_sympy_base() for var in inputs
        }
        result_value = expr.subs(base_unit_inputs).evalf()
        output_quantity = ureg(f"{result_value}")

        if output_variable.unit:
            output_quantity = output_quantity.to(output_variable.unit)

        # Format output
        decimal_fmt = ""
        if decimals is not None:
            decimal_fmt = f".{decimals}f"
        output_latex = f"{output_quantity:{decimal_fmt}~L}"

        # Build the three-step LaTeX
        output_sym_latex = latex(output_variable.symbol)
        align = "{align*}"
        full_latex = textwrap.dedent(rf"""
        $$
        \begin{align}
        {output_sym_latex} &= {expression_latex} \\
        &= {substituted_latex} \\
        {output_sym_latex} &= {output_latex}
        \end{align}
        $$
        """)

        output_variable.quantity = output_quantity
        output_variable._eval_latex = full_latex
        return output_variable


    # Monkey-patch .symeval() onto sympy expressions
    def _symeval_method(self, output_variable, inputs, decimals=None):
        """Convenience method patched onto sympy.Expr. See symeval() for docs."""
        return symeval(
            self, output_variable=output_variable, inputs=inputs, decimals=decimals
        )


    sympy.Expr.symeval = _symeval_method
    return Variable, symeval


@app.cell(column=2, hide_code=True)
def _(mo):
    mo.md(r"""
    # Tests
    """)
    return


@app.cell
def _(Q_, Variable, symeval, sympy):
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
        assert "SYMEVALPH" not in rendered
        assert "r_{y}" in rendered

    return


if __name__ == "__main__":
    app.run()
