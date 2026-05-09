import marimo

__generated_with = "0.23.5"
app = marimo.App(width="medium")


@app.cell
def _():
    import marimo as mo
    import sympy

    from symeval import Variable

    return Variable, mo, sympy


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    # Axial Resistance of Steel HSS Member

    As per CSA S16-17
    source: https://www.youtube.com/watch?v=n9Uzy3Eb-XI
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


@app.cell
def _():
    return


if __name__ == "__main__":
    app.run()
