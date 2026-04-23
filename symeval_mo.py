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

__generated_with = "0.23.2"
app = marimo.App(width="columns")


@app.cell(column=0, hide_code=True)
def _(mo):
    mo.md(r"""
    # symeval

    Symbolic evaluation for engineering calculations.

    Renders the three-step chain:
    **symbolic → numbers with units → result** as LaTeX.

    Cells marked with `## EXPORT` are extracted into a Python package via
    [`mobuild`](https://github.com/koaning/mobuild).
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
def _(Variable):
    # Define inputs
    # Loads
    compressive_force = Variable("C_f", name="Compressive force", unit="kN", value=680)

    # Member geometry
    beam_length = Variable("L", name="Beam length", unit="m", value=6.5)
    effective_length_factor = Variable(
        "k", name="Effective length factor", value=1
    )

    # Material properties
    strength_reduction_factor = Variable(
        r"\phi_s", name="Strength reduction factor", unit=None, value=0.85
    )
    elastic_modulus = Variable("E", name="Elastic modulus", unit="GPa", value=200)
    yield_strength = Variable("F_y", name="Yield strength", unit="MPa", value=400)
    n = Variable("n", name="Strain-hardening exponent", unit=None, value=1.34)

    # Member section properties
    cross_sectional_area = Variable(
        "A", name="Cross-sectional area", unit="mm^2", value=10_300
    )
    radius_gyration = Variable(
        "r_y", name="Radius of gyration about the y-axis", unit="mm", value=76.1
    )
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
def _():
    def _magnitude_cells(variables):
        """Compute max int-part and max decimal-part widths across non-None magnitudes."""
        max_int, max_dec = 0, 0
        for v in variables:
            if v.quantity is None:
                continue
            s = str(v.quantity.magnitude)
            if "." in s:
                i, d = s.split(".", 1)
                max_int = max(max_int, len(i))
                max_dec = max(max_dec, len(d))
            else:
                max_int = max(max_int, len(s))
        return max_int, max_dec


    def _format_magnitude(mag, max_int, max_dec):
        """Pad magnitude with phantoms so every number has identical visual width.

        Guarantees decimal-point alignment when the result is placed in any
        alignment column of a KaTeX array (avoids unsupported r@{}l spec).
        """
        s = str(mag)
        if "." in s:
            i, d = s.split(".", 1)
        else:
            i, d = s, ""

        left_pad = max_int - len(i)
        parts = []
        if left_pad > 0:
            parts.append(rf"\phantom{{{'0' * left_pad}}}")
        parts.append(i)
        if d:
            parts.append("." + d)
        elif max_dec > 0:
            parts.append(r"\phantom{.}")
        right_pad = max_dec - len(d)
        if right_pad > 0:
            parts.append(rf"\phantom{{{'0' * right_pad}}}")
        return "".join(parts)


    def inputs_array(inputs):
        """Render Variables as a decimal-aligned KaTeX array.

        Args:
            inputs: list[Variable] for a flat display, or dict[str, list[Variable]]
                for a grouped display with bold section headings.

        Returns:
            A mo.md-ready string wrapping the array in $$...$$.
        """
        groups = {None: inputs} if isinstance(inputs, list) else inputs
        flat = [v for vs in groups.values() for v in vs]
        max_int, max_dec = _magnitude_cells(flat)

        rows = []
        for heading, variables in groups.items():
            if heading is not None:
                rows.append(rf"\textbf{{{heading}}} & & & & \\")
            for v in variables:
                name = rf"\text{{{v.name}}}"
                sym = v.latex
                if v.quantity is None:
                    rows.append(
                        rf"{name} & {sym} & = & \multicolumn{{2}}{{c}}{{-}} \\"
                    )
                    continue
                num = _format_magnitude(v.quantity.magnitude, max_int, max_dec)
                unit = (
                    ""
                    if v.quantity.dimensionless
                    else rf"\,{format(v.quantity.units, '~L')}"
                )
                rows.append(rf"{name} & {sym} & = & {num} & {unit} \\")

        body = "\n".join(rows)
        return f"$$\n\\begin{{array}}{{llcrl}}\n{body}\n\\end{{array}}\n$$"

    return (inputs_array,)


@app.cell(hide_code=True)
def _(
    beam_length,
    compressive_force,
    cross_sectional_area,
    effective_length_factor,
    elastic_modulus,
    inputs_array,
    mo,
    n,
    radius_gyration,
    strength_reduction_factor,
    yield_strength,
):
    inputs_table_latex = inputs_array(
        {
            "Loads": [compressive_force],
            "Member geometry": [beam_length, effective_length_factor],
            "Material properties": [
                strength_reduction_factor,
                elastic_modulus,
                yield_strength,
                n,
            ],
            "Member section properties": [
                cross_sectional_area,
                radius_gyration,
            ],
        }
    )
    mo.md(rf"""
    ### Inputs
    {inputs_table_latex}
    """)
    return


@app.cell(hide_code=True)
def _(
    beam_length,
    compressive_force,
    cross_sectional_area,
    effective_length_factor,
    elastic_modulus,
    mo,
    radius_gyration,
    strength_reduction_factor,
    yield_strength,
):
    mo.md(rf"""
    ### Inputs - table with quantities

    |     |     |     |     |     |
    |--------------|--------|---|-------|---|
    | **Loads** |  |  |  |
    | {compressive_force.name} | ${compressive_force.symbol}$ | = | ${compressive_force.quantity:~L}$ |
    | **Member geometry** |  |  |  |
    | {beam_length.name} | ${beam_length.symbol}$ | = | ${beam_length.quantity:~L}$ |
    | {effective_length_factor.name} | ${effective_length_factor.symbol}$ | = | ${effective_length_factor.quantity:~L}$ |
    | **Material properties** |  |  |  |
    | {elastic_modulus.name} | ${elastic_modulus.symbol}$ | = | ${elastic_modulus.quantity:~L}$ |
    | {yield_strength.name} | ${yield_strength.symbol}$ | = | ${yield_strength.quantity:~L}$ |
    | {strength_reduction_factor.name} | ${strength_reduction_factor.symbol}$ | = | ${strength_reduction_factor.quantity:~L}$ |
    | **Member section properties** |  |  |  |
    | {cross_sectional_area.name} | ${cross_sectional_area.symbol}$ | = | ${cross_sectional_area.quantity:~L}$ |
    | {radius_gyration.name} | ${radius_gyration.symbol}$ | = | ${radius_gyration.quantity:~L}$ |

    ### Inputs - with a separate column for the units

    |     |     |     |     |     |
    |--------------|--------|---|-------|---|
    | **Loads** |  |  |  |
    | {compressive_force.name} | ${compressive_force.symbol}$ | = | ${compressive_force.value}$ | ${compressive_force.unit}$ |
    | **Member geometry** |  |  |  |
    | {beam_length.name} | ${beam_length.symbol}$ | = | ${beam_length.value}$ | ${beam_length.unit}$ |
    | {effective_length_factor.name} | ${effective_length_factor.symbol}$ | = | ${effective_length_factor.value}$ | ${effective_length_factor.unit}$ |
    | **Material properties** |  |  |  |
    | {elastic_modulus.name} | ${elastic_modulus.symbol}$ | = | ${elastic_modulus.value}$ | ${elastic_modulus.unit}$ |
    | {yield_strength.name} | ${yield_strength.symbol}$ | = | ${yield_strength.value}$ | ${yield_strength.unit}$ |
    | {strength_reduction_factor.name} | ${strength_reduction_factor.symbol}$ | = | ${strength_reduction_factor.value}$ | ${strength_reduction_factor.unit}$ |
    | **Member section properties** |  |  |  |
    | {cross_sectional_area.name} | ${cross_sectional_area.symbol}$ | = | ${cross_sectional_area.value}$ | ${cross_sectional_area.unit}$ |
    | {radius_gyration.name} | ${radius_gyration.symbol}$ | = | ${radius_gyration.value}$ | ${radius_gyration.unit}$ |

    This table could be nicer if:

    - the units in the table with a separate unit column weren't italic. Please also explain why the inputs table with the quantities aren't written in italic;
    - the column with the units aligned left. Why do the columns in these tables align right in the first place?
    - Would it be a good idea to add a .md_table_row attribute or property to the Variables, such that I can create these kind of tables in that way?
    """)
    return


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


@app.cell
def _(Variable, axial_resistance, compressive_force):
    dcr_expr = compressive_force.symbol / axial_resistance.symbol
    dcr = dcr_expr.symeval(
        output_variable=Variable("DCR", name="Demand capacity ratio", unit=None),
        inputs=[compressive_force, axial_resistance],
        decimals=3,
    )
    dcr
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    Things that could be better:

    - Decimal places in the filled in formula should be decimal or maybe at maximum decimals + 1.
    - Would be handier if it were also possible to create sympy expressions from Variables directly, instead of having to call .symbol on every variable when creating an expression.
    - Would be handier if the inputs kwarg wasn't needed when the expression is made up of Variables. It shouldn't be necessary to supply a list of inputs I would say, because it's already given in the expression. However, when I'm doing symbolic math with sympy first and then want to substitute in Variables and evaluate at the end, then I will have to supply a list of inputs to the .symeval method, because the resulting expression only contains sympy.Symbols, that don't contain values or units, right?
    - When the output_variable is not dimensionless or when the unit is not and SI base unit, then always display the SI base unit, and then the Variable unit like Symbol = Value output_variable.base_unit = Value output_variable.unit
    - Add verbose flag that adds an additional line to the substitutions that shows the expression with numbers in SI base units, before showing the line with the result. The line with the SI base units should use scientific notation to prevent illegible numbers. Possibly it would be good to use a [SciForm's](https://sciform.readthedocs.io/en/stable) engineering formatter with exp_mode="engineering" in a custom Pint formatter (see last paragraph of https://pint.readthedocs.io/en/stable/user/formatting.html). But let's implement the verbose flag first and then look at the engineering formatting. The engineering formatting also allows for significant figures, which might actually be something that should be attached to the Variables.

    ### Way of working

    When developing things, I'd like to work from a practical application. So let's always first think of a practical use case and example calculation with known results, then set up the tests, and then implement. Put this into the CLAUDE.md under a sensible heading and formulated in a sensible way.
    """)
    return


@app.cell(column=1, hide_code=True)
def _(mo):
    mo.md(r"""
    # Implementation
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
                return f"{self.name}: {self.latex} = {self.quantity:~L}"
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
