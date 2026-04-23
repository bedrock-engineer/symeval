import marimo

__generated_with = "0.23.2"
app = marimo.App(width="medium")


@app.cell
def _():
    import marimo as mo
    import sympy as sp

    from symeval import Variable, symeval

    return Variable, mo, sp, symeval


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    # Axial Resistance of Steel HSS Member

    As per CSA S16-17
    source: https://www.youtube.com/watch?v=n9Uzy3Eb-XI
    """)
    return


@app.cell
def _(Variable):
    # Loads
    c_f = Variable("C_f", name="Compressive force", value=275, unit="kN")

    # Member geometry
    beam_length = Variable("L", name="Beam length", value=6.5, unit="m")
    effective_length_factor = Variable("k", name="Effective length factor", value=1)

    # Material properties
    strength_reduction_factor = Variable(r"\phi_s", name="Strength reduction factor", value=0.85)
    elastic_modulus = Variable("E", name="Elastic modulus", value=200, unit="GPa")
    yield_strength = Variable("F_y", name="Yield strength", value=400, unit="MPa")
    n = Variable("n", name="Strain-hardening exponent", value=1.34)

    # Member section properties
    cross_sectional_area = Variable("A", name="Cross-sectional area", value=10_300, unit="mm^2")
    radius_gyration = Variable(
        "r_y", name="Radius of gyration about the y-axis", value=76.1, unit="mm"
    )
    return (
        beam_length,
        c_f,
        cross_sectional_area,
        effective_length_factor,
        elastic_modulus,
        radius_gyration,
        strength_reduction_factor,
        yield_strength,
    )


@app.cell(hide_code=True)
def _(
    beam_length,
    c_f,
    cross_sectional_area,
    effective_length_factor,
    elastic_modulus,
    mo,
    radius_gyration,
    strength_reduction_factor,
    yield_strength,
):
    mo.md(rf"""
    |     |     |     |     |
    |--------------|--------|---|-------|
    | **Loads** |  |  |  |
    | {c_f.name} | ${c_f.symbol}$ | = | ${c_f.quantity:~L}$ |
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
    """)
    return


@app.cell
def _(
    F_e,
    beam_length,
    effective_length_factor,
    elastic_modulus,
    euler_buckling_expr,
    radius_gyration,
):
    result = euler_buckling_expr.symeval(
        output=F_e,
        inputs=[effective_length_factor, elastic_modulus, beam_length, radius_gyration],
        unit="GPa",
        decimals=3,
    )
    result
    return (result,)


@app.cell
def _(result):
    result.latex
    return


@app.cell
def _(
    Variable,
    beam_length,
    effective_length_factor,
    elastic_modulus,
    radius_gyration,
    sp,
    symeval,
):
    F_e = Variable("F_e", name="Euler buckling stress")

    euler_buckling_expr = (sp.pi**2 * elastic_modulus.sym) / (
        (effective_length_factor.sym * beam_length.sym / radius_gyration.sym) ** 2
    )

    buckling_result = symeval(
        euler_buckling_expr,
        output=F_e,
        inputs=[effective_length_factor, elastic_modulus, beam_length, radius_gyration],
        unit="GPa",
        decimals=3,
    )

    buckling_result.__repr__
    return F_e, euler_buckling_expr


if __name__ == "__main__":
    app.run()
