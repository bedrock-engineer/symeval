# /// script
# requires-python = ">=3.12"
# dependencies = [
#     "marimo",
#     "numpy",
#     "pint",
#     "plotly",
#     "symeval",
#     "sympy",
# ]
# ///

import marimo

__generated_with = "0.24.0"
app = marimo.App()


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    # Simply supported beam

    Closed-form bending moment and shear diagrams for a simply supported
    beam, worked with [SymEval](https://github.com/bedrock-engineer/symeval),
    in the spirit of CalcpadCE's
    [Simply Supported Beam](https://imartincei.github.io/CalcpadCE/examples/simply-supported-beams.html)
    reference page.

    Sign convention: $x$ is measured from the left support, a downward load
    is positive, and a sagging moment is positive.

    ## Uniformly distributed load

    A beam of length $L$, pinned at both ends, carries a uniformly
    distributed load $w$ (force per unit length) over its full span.
    Adjust the length and load below.

    ![Simply supported beam with a uniformly distributed load](public/simply-supported-beam-distributed-load-uniform.png)
    *Schematic: CalcpadCE (MIT License)*
    """)
    return


@app.cell
def _():
    import marimo as mo
    import numpy as np
    import pint
    import plotly.graph_objects as go
    import sympy
    from pint import Quantity
    from plotly.subplots import make_subplots
    from sympy import Eq, Piecewise, Symbol, sqrt

    import symeval  # noqa: F401  (registers .sym_evalf / .quantity_evalf on sympy)

    return (
        Eq,
        Piecewise,
        Quantity,
        Symbol,
        go,
        make_subplots,
        mo,
        np,
        pint,
        sqrt,
        sympy,
    )


@app.cell
def _(mo):
    length_slider = mo.ui.slider(
        start=1,
        stop=20,
        step=0.5,
        value=6,
        debounce=True,
        include_input=True,
        label="Beam length L (m)",
    )
    load_slider = mo.ui.slider(
        start=1,
        stop=50,
        step=0.5,
        value=12,
        debounce=True,
        include_input=True,
        label="Distributed load w (kN/m)",
    )
    mo.hstack([length_slider, load_slider], align="center", justify="center", gap=2)
    return length_slider, load_slider


@app.cell
def _(Symbol):
    L = Symbol("L")
    w = Symbol("w")
    return L, w


@app.cell
def _(L, Quantity, length_slider, load_slider, w):
    beam_inputs = {
        L: Quantity(length_slider.value, "m"),
        w: Quantity(load_slider.value, "kN/m"),
    }
    return (beam_inputs,)


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ### Maximum bending moment and shear force

    For a UDL over the full span, the maximum moment occurs at midspan
    and the maximum shear occurs at the supports:
    """)
    return


@app.cell
def _(Eq, L, Symbol, w):
    m_max_eq = Eq(Symbol("M_max"), w * L**2 / 8)
    v_max_eq = Eq(Symbol("V_max"), w * L / 2)
    return m_max_eq, v_max_eq


@app.cell
def _(beam_inputs, m_max_eq, mo, v_max_eq):
    m_max_result = m_max_eq.sym_evalf(subs=beam_inputs, output_unit="kN*m")
    v_max_result = v_max_eq.sym_evalf(subs=beam_inputs, output_unit="kN")
    mo.vstack([m_max_result, v_max_result], align="start", gap=1)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ### Bending moment and shear as functions of position
    """)
    return


@app.cell
def _(L, Piecewise, Symbol, w):
    x = Symbol("x")
    m_of_x = w * L / 2 * x - w * x**2 / 2
    v_of_x = w * L / 2 - w * x
    # Piecewise, not just m_of_x/v_of_x, so that a future partial-load or point-load
    # case is just more (expr, condition) clauses here. The per-segment expressions
    # (m_of_x, v_of_x) are kept as plain sympy.Expr and reused directly for every
    # sym_evalf/quantity_evalf call below: those go through pint-unit substitution,
    # and a Piecewise's relational conditions (e.g. x <= L) can't be decided once x
    # and L are unit-bearing sympy expressions rather than plain floats, so it never
    # collapses to a branch (symeval issue #4:
    # https://github.com/bedrock-engineer/symeval/issues/4). Piecewise itself is
    # only used for display (below) and for lambdify-based plotting, both of which
    # never go through symeval's unit machinery.
    m_expr = Piecewise((m_of_x, (x >= 0) & (x <= L)))
    v_expr = Piecewise((v_of_x, (x >= 0) & (x <= L)))
    return m_expr, m_of_x, v_expr, v_of_x, x


@app.cell
def _(Eq, Symbol, m_expr, mo, sympy, v_expr):
    mo.vstack(
        [
            mo.md(rf"$\displaystyle {sympy.latex(Eq(Symbol('M(x)'), m_expr))}$"),
            mo.md(rf"$\displaystyle {sympy.latex(Eq(Symbol('V(x)'), v_expr))}$"),
        ]
    )
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ### Diagrams
    """)
    return


@app.cell
def _(length_slider, mo):
    x1_slider = mo.ui.slider(
        start=0,
        stop=length_slider.value,
        step=length_slider.value / 100,
        value=length_slider.value / 2,
        debounce=True,
        include_input=True,
        label="Probe point x_1 (m)",
    )
    return (x1_slider,)


@app.cell
def _(
    L,
    go,
    length_slider,
    load_slider,
    m_expr,
    make_subplots,
    np,
    sympy,
    v_expr,
    w,
    x,
    x1_slider,
):
    _L_val = length_slider.value
    _w_val = load_slider.value
    _x_vals = np.linspace(0, _L_val, 200)

    # w, L are already plain floats here (from the sliders), so the Piecewise's
    # conditions compare plain numbers, not pint-derived unit expressions: lambdify
    # can turn it into a vectorised numpy function directly, no unit bookkeeping
    # needed since the slider units (m, kN/m) already combine into kN*m / kN.
    _m_func = sympy.lambdify(x, m_expr.subs({L: _L_val, w: _w_val}), "numpy")
    _v_func = sympy.lambdify(x, v_expr.subs({L: _L_val, w: _w_val}), "numpy")
    _m_vals = np.asarray(_m_func(_x_vals), dtype=float)
    _v_vals = np.asarray(_v_func(_x_vals), dtype=float)

    def _rgba(hex_color, alpha):
        hex_color = hex_color.lstrip("#")
        _r, _g, _b = (int(hex_color[i : i + 2], 16) for i in (0, 2, 4))
        return f"rgba({_r}, {_g}, {_b}, {alpha})"

    _m_color = "#4C72B0"
    _v_color = "#C44E52"

    _fig = make_subplots(
        rows=2,
        cols=1,
        shared_xaxes=True,
        subplot_titles=("Bending moment diagram", "Shear force diagram"),
        vertical_spacing=0.12,
    )

    _fig.add_trace(
        go.Scatter(
            x=_x_vals,
            y=_m_vals,
            mode="lines",
            name="M(x)",
            line=dict(color=_m_color, width=2),
            fill="tozeroy",
            fillcolor=_rgba(_m_color, 0.12),
            showlegend=False,
        ),
        row=1,
        col=1,
    )
    _fig.add_trace(
        go.Scatter(
            x=_x_vals,
            y=_v_vals,
            mode="lines",
            name="V(x)",
            line=dict(color=_v_color, width=2),
            fill="tozeroy",
            fillcolor=_rgba(_v_color, 0.12),
            showlegend=False,
        ),
        row=2,
        col=1,
    )

    _x1_val = x1_slider.value
    _m_at_x1 = float(_m_func(_x1_val))
    _v_at_x1 = float(_v_func(_x1_val))

    for _row, _val in ((1, _m_at_x1), (2, _v_at_x1)):
        _fig.add_vline(x=_x1_val, line=dict(color="grey", dash="dash", width=1), row=_row, col=1)
        _fig.add_trace(
            go.Scatter(
                x=[_x1_val],
                y=[_val],
                mode="markers",
                marker=dict(color="black", size=8),
                showlegend=False,
            ),
            row=_row,
            col=1,
        )
        _fig.add_hline(y=0, line=dict(color="black", width=0.8), row=_row, col=1)

    _fig.update_yaxes(title_text="M (kN·m)", autorange="reversed", row=1, col=1)
    _fig.update_yaxes(title_text="V (kN)", row=2, col=1)
    _fig.update_xaxes(title_text="x (m)", row=2, col=1)
    _fig.update_layout(height=600, margin=dict(t=60, b=40), template="plotly_white")

    _fig
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ### Probe the diagrams at a point
    """)
    return


@app.cell
def _(x1_slider):
    x1_slider
    return


@app.cell
def _(
    Eq,
    Quantity,
    Symbol,
    beam_inputs,
    m_of_x,
    mo,
    pint,
    v_of_x,
    x,
    x1_slider,
):
    probe_inputs = beam_inputs | {x: Quantity(x1_slider.value, "m")}
    m_probe_eq = Eq(Symbol("M_{x_1}"), m_of_x)
    v_probe_eq = Eq(Symbol("V_{x_1}"), v_of_x)

    # An exactly-zero result (V at midspan, M at a support) loses its unit inside
    # quantity_evalf and then can't convert to output_unit (symeval issue #5:
    # https://github.com/bedrock-engineer/symeval/issues/5). Falling back to no
    # output_unit keeps the SI-base (still dimensionless-looking, but non-crashing)
    # zero instead of raising.
    try:
        m_probe_result = m_probe_eq.sym_evalf(subs=probe_inputs, output_unit="kN*m")
    except pint.errors.DimensionalityError:
        m_probe_result = m_probe_eq.sym_evalf(subs=probe_inputs)
    try:
        v_probe_result = v_probe_eq.sym_evalf(subs=probe_inputs, output_unit="kN")
    except pint.errors.DimensionalityError:
        v_probe_result = v_probe_eq.sym_evalf(subs=probe_inputs)

    mo.vstack([m_probe_result, v_probe_result], align="start", gap=1)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Concentrated force

    A beam of length $L$, pinned at both ends, carries a single point load
    $P$ at a distance $a$ from the left support. Adjust the length, load
    and position below.

    ![Simply supported beam with a concentrated force](public/simply-supported-beam-concentrated-force.png)
    *Schematic: CalcpadCE (MIT License)*
    """)
    return


@app.cell
def _(mo):
    cf_length_slider = mo.ui.slider(
        start=1,
        stop=20,
        step=0.5,
        value=6,
        debounce=True,
        include_input=True,
        label="Beam length L (m)",
    )
    cf_force_slider = mo.ui.slider(
        start=1,
        stop=200,
        step=1,
        value=50,
        debounce=True,
        include_input=True,
        label="Point load P (kN)",
    )
    mo.hstack([cf_length_slider, cf_force_slider], align="center", justify="center", gap=2)
    return cf_force_slider, cf_length_slider


@app.cell
def _(cf_length_slider, mo):
    cf_pos_slider = mo.ui.slider(
        start=0,
        stop=cf_length_slider.value,
        step=cf_length_slider.value / 100,
        value=cf_length_slider.value / 2,
        debounce=True,
        include_input=True,
        label="Load position a (m)",
    )
    cf_pos_slider
    return (cf_pos_slider,)


@app.cell
def _(Symbol):
    P = Symbol("P")
    a = Symbol("a")
    return P, a


@app.cell
def _(L, P, Quantity, a, cf_force_slider, cf_length_slider, cf_pos_slider):
    cf_inputs = {
        L: Quantity(cf_length_slider.value, "m"),
        P: Quantity(cf_force_slider.value, "kN"),
        a: Quantity(cf_pos_slider.value, "m"),
    }
    return (cf_inputs,)


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ### Maximum bending moment and shear force

    The maximum moment occurs under the load; the maximum shear equals
    whichever support reaction is larger (the support closer to the load):
    """)
    return


@app.cell
def _(Eq, L, P, Symbol, a, cf_length_slider, cf_pos_slider):
    cf_m_max_eq = Eq(Symbol("M_max"), P * a * (L - a) / L)
    # Which reaction governs is decided here on the plain slider floats (not a
    # sympy relational on unit-bearing substitutions - see the Piecewise note
    # below), so the picked formula still renders and evaluates through the
    # normal, safe sym_evalf path.
    if cf_pos_slider.value <= cf_length_slider.value / 2:
        cf_v_max_eq = Eq(Symbol("V_max"), P * (L - a) / L)
    else:
        cf_v_max_eq = Eq(Symbol("V_max"), P * a / L)
    return cf_m_max_eq, cf_v_max_eq


@app.cell
def _(cf_inputs, cf_m_max_eq, cf_v_max_eq, mo, pint):
    # M_max is exactly zero when the load sits right on a support (a = 0 or a = L):
    # symeval issue #5 again (https://github.com/bedrock-engineer/symeval/issues/5).
    try:
        cf_m_max_result = cf_m_max_eq.sym_evalf(subs=cf_inputs, output_unit="kN*m")
    except pint.errors.DimensionalityError:
        cf_m_max_result = cf_m_max_eq.sym_evalf(subs=cf_inputs)
    cf_v_max_result = cf_v_max_eq.sym_evalf(subs=cf_inputs, output_unit="kN")
    mo.vstack([cf_m_max_result, cf_v_max_result], align="start", gap=1)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ### Bending moment and shear as functions of position
    """)
    return


@app.cell
def _(L, P, Piecewise, a, x):
    cf_m_of_x_left = P * (L - a) / L * x
    cf_m_of_x_right = P * (L - a) / L * x - P * (x - a)
    cf_v_of_x_left = P * (L - a) / L
    cf_v_of_x_right = P * (L - a) / L - P

    # Two segments split at the load position a; see the UDL section's note on
    # why Piecewise never goes through sym_evalf/quantity_evalf directly
    # (symeval issue #4: https://github.com/bedrock-engineer/symeval/issues/4).
    cf_m_expr = Piecewise(
        (cf_m_of_x_left, (x >= 0) & (x <= a)),
        (cf_m_of_x_right, (x > a) & (x <= L)),
    )
    cf_v_expr = Piecewise(
        (cf_v_of_x_left, (x >= 0) & (x <= a)),
        (cf_v_of_x_right, (x > a) & (x <= L)),
    )
    return cf_m_expr, cf_m_of_x_left, cf_m_of_x_right, cf_v_expr, cf_v_of_x_left, cf_v_of_x_right


@app.cell
def _(Eq, Symbol, cf_m_expr, cf_v_expr, mo, sympy):
    mo.vstack(
        [
            mo.md(rf"$\displaystyle {sympy.latex(Eq(Symbol('M(x)'), cf_m_expr))}$"),
            mo.md(rf"$\displaystyle {sympy.latex(Eq(Symbol('V(x)'), cf_v_expr))}$"),
        ]
    )
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ### Diagrams
    """)
    return


@app.cell
def _(cf_length_slider, mo):
    cf_x1_slider = mo.ui.slider(
        start=0,
        stop=cf_length_slider.value,
        step=cf_length_slider.value / 100,
        value=cf_length_slider.value / 2,
        debounce=True,
        include_input=True,
        label="Probe point x_1 (m)",
    )
    return (cf_x1_slider,)


@app.cell
def _(
    L,
    P,
    a,
    cf_force_slider,
    cf_length_slider,
    cf_m_expr,
    cf_pos_slider,
    cf_v_expr,
    cf_x1_slider,
    go,
    make_subplots,
    np,
    sympy,
    x,
):
    _L_val = cf_length_slider.value
    _P_val = cf_force_slider.value
    _a_val = cf_pos_slider.value
    _x_vals = np.linspace(0, _L_val, 200)

    _m_func = sympy.lambdify(x, cf_m_expr.subs({L: _L_val, P: _P_val, a: _a_val}), "numpy")
    _v_func = sympy.lambdify(x, cf_v_expr.subs({L: _L_val, P: _P_val, a: _a_val}), "numpy")
    _m_vals = np.asarray(_m_func(_x_vals), dtype=float)
    _v_vals = np.asarray(_v_func(_x_vals), dtype=float)

    def _rgba(hex_color, alpha):
        hex_color = hex_color.lstrip("#")
        _r, _g, _b = (int(hex_color[i : i + 2], 16) for i in (0, 2, 4))
        return f"rgba({_r}, {_g}, {_b}, {alpha})"

    _m_color = "#4C72B0"
    _v_color = "#C44E52"

    _fig = make_subplots(
        rows=2,
        cols=1,
        shared_xaxes=True,
        subplot_titles=("Bending moment diagram", "Shear force diagram"),
        vertical_spacing=0.12,
    )

    _fig.add_trace(
        go.Scatter(
            x=_x_vals,
            y=_m_vals,
            mode="lines",
            line=dict(color=_m_color, width=2),
            fill="tozeroy",
            fillcolor=_rgba(_m_color, 0.12),
            showlegend=False,
        ),
        row=1,
        col=1,
    )
    _fig.add_trace(
        go.Scatter(
            x=_x_vals,
            y=_v_vals,
            mode="lines",
            line=dict(color=_v_color, width=2),
            fill="tozeroy",
            fillcolor=_rgba(_v_color, 0.12),
            showlegend=False,
        ),
        row=2,
        col=1,
    )

    _x1_val = cf_x1_slider.value
    _m_at_x1 = float(_m_func(_x1_val))
    _v_at_x1 = float(_v_func(_x1_val))

    for _row, _val in ((1, _m_at_x1), (2, _v_at_x1)):
        _fig.add_vline(x=_x1_val, line=dict(color="grey", dash="dash", width=1), row=_row, col=1)
        _fig.add_trace(
            go.Scatter(
                x=[_x1_val],
                y=[_val],
                mode="markers",
                marker=dict(color="black", size=8),
                showlegend=False,
            ),
            row=_row,
            col=1,
        )
        _fig.add_hline(y=0, line=dict(color="black", width=0.8), row=_row, col=1)

    _fig.update_yaxes(title_text="M (kN·m)", autorange="reversed", row=1, col=1)
    _fig.update_yaxes(title_text="V (kN)", row=2, col=1)
    _fig.update_xaxes(title_text="x (m)", row=2, col=1)
    _fig.update_layout(height=600, margin=dict(t=60, b=40), template="plotly_white")

    _fig
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ### Probe the diagrams at a point
    """)
    return


@app.cell
def _(cf_x1_slider):
    cf_x1_slider
    return


@app.cell
def _(Eq, Quantity, Symbol, a, cf_inputs, cf_m_of_x_left, cf_m_of_x_right, cf_v_of_x_left, cf_v_of_x_right, cf_x1_slider, mo, pint, x):
    cf_probe_inputs = cf_inputs | {x: Quantity(cf_x1_slider.value, "m")}

    # Which branch applies is decided on the plain slider floats, mirroring
    # Piecewise's own condition but never running it through sym_evalf/
    # quantity_evalf (symeval issue #4).
    if cf_x1_slider.value <= cf_inputs[a].magnitude:
        cf_m_branch, cf_v_branch = cf_m_of_x_left, cf_v_of_x_left
    else:
        cf_m_branch, cf_v_branch = cf_m_of_x_right, cf_v_of_x_right

    cf_m_probe_eq = Eq(Symbol("M_{x_1}"), cf_m_branch)
    cf_v_probe_eq = Eq(Symbol("V_{x_1}"), cf_v_branch)

    # Exact-zero fallback: symeval issue #5 (e.g. M(x_1) at either support).
    try:
        cf_m_probe_result = cf_m_probe_eq.sym_evalf(subs=cf_probe_inputs, output_unit="kN*m")
    except pint.errors.DimensionalityError:
        cf_m_probe_result = cf_m_probe_eq.sym_evalf(subs=cf_probe_inputs)
    try:
        cf_v_probe_result = cf_v_probe_eq.sym_evalf(subs=cf_probe_inputs, output_unit="kN")
    except pint.errors.DimensionalityError:
        cf_v_probe_result = cf_v_probe_eq.sym_evalf(subs=cf_probe_inputs)

    mo.vstack([cf_m_probe_result, cf_v_probe_result], align="start", gap=1)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Concentrated moment

    A beam of length $L$, pinned at both ends, carries a clockwise
    applied moment $M_0$ at a distance $a$ from the left support. Unlike a
    force, a pure moment does not change the shear along the span - it only
    shifts the bending moment, by exactly $M_0$, at the point it's applied.

    ![Simply supported beam with a concentrated moment](public/simply-supported-beam-concentrated-moment.png)
    *Schematic: CalcpadCE (MIT License)*
    """)
    return


@app.cell
def _(mo):
    cm_length_slider = mo.ui.slider(
        start=1,
        stop=20,
        step=0.5,
        value=6,
        debounce=True,
        include_input=True,
        label="Beam length L (m)",
    )
    cm_moment_slider = mo.ui.slider(
        start=1,
        stop=200,
        step=1,
        value=50,
        debounce=True,
        include_input=True,
        label="Applied moment M_0 (kN*m)",
    )
    mo.hstack([cm_length_slider, cm_moment_slider], align="center", justify="center", gap=2)
    return cm_length_slider, cm_moment_slider


@app.cell
def _(cm_length_slider, mo):
    cm_pos_slider = mo.ui.slider(
        start=0,
        stop=cm_length_slider.value,
        step=cm_length_slider.value / 100,
        value=cm_length_slider.value / 2,
        debounce=True,
        include_input=True,
        label="Moment position a (m)",
    )
    cm_pos_slider
    return (cm_pos_slider,)


@app.cell
def _(Symbol):
    cm_M0 = Symbol("M_0")
    cm_a = Symbol("a")
    return cm_M0, cm_a


@app.cell
def _(L, Quantity, cm_M0, cm_a, cm_length_slider, cm_moment_slider, cm_pos_slider):
    cm_inputs = {
        L: Quantity(cm_length_slider.value, "m"),
        cm_M0: Quantity(cm_moment_slider.value, "kN*m"),
        cm_a: Quantity(cm_pos_slider.value, "m"),
    }
    return (cm_inputs,)


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ### Maximum bending moment and shear force

    The moment jumps by $M_0$ right at $x=a$; the larger-magnitude side of
    that jump is $M_{max}$ (it can come out hogging, i.e. negative, when $a$
    is past midspan). Shear is the same constant value everywhere:
    """)
    return


@app.cell
def _(Eq, L, Symbol, cm_M0, cm_a, cm_length_slider, cm_pos_slider):
    if cm_pos_slider.value <= cm_length_slider.value / 2:
        cm_m_max_eq = Eq(Symbol("M_max"), cm_M0 * (L - cm_a) / L)
    else:
        cm_m_max_eq = Eq(Symbol("M_max"), -cm_M0 * cm_a / L)
    cm_v_max_eq = Eq(Symbol("V_max"), cm_M0 / L)
    return cm_m_max_eq, cm_v_max_eq


@app.cell
def _(cm_inputs, cm_m_max_eq, cm_v_max_eq, mo):
    cm_m_max_result = cm_m_max_eq.sym_evalf(subs=cm_inputs, output_unit="kN*m")
    cm_v_max_result = cm_v_max_eq.sym_evalf(subs=cm_inputs, output_unit="kN")
    mo.vstack([cm_m_max_result, cm_v_max_result], align="start", gap=1)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ### Bending moment and shear as functions of position
    """)
    return


@app.cell
def _(L, Piecewise, cm_M0, cm_a, x):
    cm_m_of_x_left = -cm_M0 / L * x
    cm_m_of_x_right = -cm_M0 / L * x + cm_M0
    cm_v_of_x = -cm_M0 / L  # constant: a pure moment doesn't change the shear.

    cm_m_expr = Piecewise(
        (cm_m_of_x_left, (x >= 0) & (x <= cm_a)),
        (cm_m_of_x_right, (x > cm_a) & (x <= L)),
    )
    return cm_m_expr, cm_m_of_x_left, cm_m_of_x_right, cm_v_of_x


@app.cell
def _(Eq, Symbol, cm_m_expr, cm_v_of_x, mo, sympy):
    mo.vstack(
        [
            mo.md(rf"$\displaystyle {sympy.latex(Eq(Symbol('M(x)'), cm_m_expr))}$"),
            mo.md(rf"$\displaystyle {sympy.latex(Eq(Symbol('V(x)'), cm_v_of_x))}$"),
        ]
    )
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ### Diagrams
    """)
    return


@app.cell
def _(cm_length_slider, mo):
    cm_x1_slider = mo.ui.slider(
        start=0,
        stop=cm_length_slider.value,
        step=cm_length_slider.value / 100,
        value=cm_length_slider.value / 2,
        debounce=True,
        include_input=True,
        label="Probe point x_1 (m)",
    )
    return (cm_x1_slider,)


@app.cell
def _(
    L,
    cm_M0,
    cm_a,
    cm_length_slider,
    cm_m_expr,
    cm_moment_slider,
    cm_pos_slider,
    cm_v_of_x,
    cm_x1_slider,
    go,
    make_subplots,
    np,
    sympy,
    x,
):
    _L_val = cm_length_slider.value
    _M0_val = cm_moment_slider.value
    _a_val = cm_pos_slider.value
    _x_vals = np.linspace(0, _L_val, 200)

    _m_func = sympy.lambdify(x, cm_m_expr.subs({L: _L_val, cm_M0: _M0_val, cm_a: _a_val}), "numpy")
    _m_vals = np.asarray(_m_func(_x_vals), dtype=float)
    # V(x) has no x-dependence at all, so lambdify would hand back a bare
    # scalar instead of an array; broadcast it to the plotted x-range by hand.
    _v_val = float(cm_v_of_x.subs({L: _L_val, cm_M0: _M0_val}))
    _v_vals = np.full_like(_x_vals, _v_val)

    def _rgba(hex_color, alpha):
        hex_color = hex_color.lstrip("#")
        _r, _g, _b = (int(hex_color[i : i + 2], 16) for i in (0, 2, 4))
        return f"rgba({_r}, {_g}, {_b}, {alpha})"

    _m_color = "#4C72B0"
    _v_color = "#C44E52"

    _fig = make_subplots(
        rows=2,
        cols=1,
        shared_xaxes=True,
        subplot_titles=("Bending moment diagram", "Shear force diagram"),
        vertical_spacing=0.12,
    )

    _fig.add_trace(
        go.Scatter(
            x=_x_vals,
            y=_m_vals,
            mode="lines",
            line=dict(color=_m_color, width=2),
            fill="tozeroy",
            fillcolor=_rgba(_m_color, 0.12),
            showlegend=False,
        ),
        row=1,
        col=1,
    )
    _fig.add_trace(
        go.Scatter(
            x=_x_vals,
            y=_v_vals,
            mode="lines",
            line=dict(color=_v_color, width=2),
            fill="tozeroy",
            fillcolor=_rgba(_v_color, 0.12),
            showlegend=False,
        ),
        row=2,
        col=1,
    )

    _x1_val = cm_x1_slider.value
    _m_at_x1 = float(_m_func(_x1_val))

    _fig.add_vline(x=_x1_val, line=dict(color="grey", dash="dash", width=1), row=1, col=1)
    _fig.add_trace(
        go.Scatter(
            x=[_x1_val],
            y=[_m_at_x1],
            mode="markers",
            marker=dict(color="black", size=8),
            showlegend=False,
        ),
        row=1,
        col=1,
    )
    _fig.add_vline(x=_x1_val, line=dict(color="grey", dash="dash", width=1), row=2, col=1)
    _fig.add_hline(y=0, line=dict(color="black", width=0.8), row=1, col=1)
    _fig.add_hline(y=0, line=dict(color="black", width=0.8), row=2, col=1)

    _fig.update_yaxes(title_text="M (kN·m)", autorange="reversed", row=1, col=1)
    _fig.update_yaxes(title_text="V (kN)", row=2, col=1)
    _fig.update_xaxes(title_text="x (m)", row=2, col=1)
    _fig.update_layout(height=600, margin=dict(t=60, b=40), template="plotly_white")

    _fig
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ### Probe the diagrams at a point
    """)
    return


@app.cell
def _(cm_x1_slider):
    cm_x1_slider
    return


@app.cell
def _(
    Eq,
    Quantity,
    Symbol,
    cm_a,
    cm_inputs,
    cm_m_of_x_left,
    cm_m_of_x_right,
    cm_v_of_x,
    cm_x1_slider,
    mo,
    pint,
    x,
):
    cm_probe_inputs = cm_inputs | {x: Quantity(cm_x1_slider.value, "m")}

    if cm_x1_slider.value <= cm_inputs[cm_a].magnitude:
        cm_m_branch = cm_m_of_x_left
    else:
        cm_m_branch = cm_m_of_x_right

    cm_m_probe_eq = Eq(Symbol("M_{x_1}"), cm_m_branch)
    cm_v_probe_eq = Eq(Symbol("V_{x_1}"), cm_v_of_x)

    # Exact-zero fallback: symeval issue #5 (M(x_1) at either support).
    try:
        cm_m_probe_result = cm_m_probe_eq.sym_evalf(subs=cm_probe_inputs, output_unit="kN*m")
    except pint.errors.DimensionalityError:
        cm_m_probe_result = cm_m_probe_eq.sym_evalf(subs=cm_probe_inputs)
    cm_v_probe_result = cm_v_probe_eq.sym_evalf(subs=cm_probe_inputs, output_unit="kN")

    mo.vstack([cm_m_probe_result, cm_v_probe_result], align="start", gap=1)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Linearly distributed load

    A beam of length $L$, pinned at both ends, carries a load that varies
    linearly from $0$ at the left support to $w_0$ at the right support.
    Adjust the length and peak load below.

    ![Simply supported beam with a linearly distributed load](public/simply-supported-beam-distributed-load-linear.png)
    *Schematic: CalcpadCE (MIT License)*
    """)
    return


@app.cell
def _(mo):
    lin_length_slider = mo.ui.slider(
        start=1,
        stop=20,
        step=0.5,
        value=6,
        debounce=True,
        include_input=True,
        label="Beam length L (m)",
    )
    lin_load_slider = mo.ui.slider(
        start=1,
        stop=50,
        step=0.5,
        value=12,
        debounce=True,
        include_input=True,
        label="Peak load w_0 (kN/m)",
    )
    mo.hstack([lin_length_slider, lin_load_slider], align="center", justify="center", gap=2)
    return lin_length_slider, lin_load_slider


@app.cell
def _(Symbol):
    lin_w0 = Symbol("w_0")
    return (lin_w0,)


@app.cell
def _(L, Quantity, lin_length_slider, lin_load_slider, lin_w0):
    lin_inputs = {
        L: Quantity(lin_length_slider.value, "m"),
        lin_w0: Quantity(lin_load_slider.value, "kN/m"),
    }
    return (lin_inputs,)


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ### Maximum bending moment and shear force

    The maximum shear is the reaction under the heavier (right) end; the
    maximum moment occurs where the shear crosses zero, at
    $x=L/\sqrt{3}\approx 0.577L$:
    """)
    return


@app.cell
def _(Eq, L, Symbol, lin_w0, sqrt):
    lin_m_max_eq = Eq(Symbol("M_max"), lin_w0 * L**2 * sqrt(3) / 27)
    lin_v_max_eq = Eq(Symbol("V_max"), lin_w0 * L / 3)
    return lin_m_max_eq, lin_v_max_eq


@app.cell
def _(lin_inputs, lin_m_max_eq, lin_v_max_eq, mo):
    lin_m_max_result = lin_m_max_eq.sym_evalf(subs=lin_inputs, output_unit="kN*m")
    lin_v_max_result = lin_v_max_eq.sym_evalf(subs=lin_inputs, output_unit="kN")
    mo.vstack([lin_m_max_result, lin_v_max_result], align="start", gap=1)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ### Bending moment and shear as functions of position
    """)
    return


@app.cell
def _(L, Piecewise, lin_w0, x):
    lin_m_of_x = lin_w0 * L / 6 * x - lin_w0 * x**3 / (6 * L)
    lin_v_of_x = lin_w0 * L / 6 - lin_w0 * x**2 / (2 * L)
    lin_m_expr = Piecewise((lin_m_of_x, (x >= 0) & (x <= L)))
    lin_v_expr = Piecewise((lin_v_of_x, (x >= 0) & (x <= L)))
    return lin_m_expr, lin_m_of_x, lin_v_expr, lin_v_of_x


@app.cell
def _(Eq, Symbol, lin_m_expr, lin_v_expr, mo, sympy):
    mo.vstack(
        [
            mo.md(rf"$\displaystyle {sympy.latex(Eq(Symbol('M(x)'), lin_m_expr))}$"),
            mo.md(rf"$\displaystyle {sympy.latex(Eq(Symbol('V(x)'), lin_v_expr))}$"),
        ]
    )
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ### Diagrams
    """)
    return


@app.cell
def _(lin_length_slider, mo):
    lin_x1_slider = mo.ui.slider(
        start=0,
        stop=lin_length_slider.value,
        step=lin_length_slider.value / 100,
        value=lin_length_slider.value / 2,
        debounce=True,
        include_input=True,
        label="Probe point x_1 (m)",
    )
    return (lin_x1_slider,)


@app.cell
def _(
    L,
    go,
    lin_length_slider,
    lin_load_slider,
    lin_m_expr,
    lin_v_expr,
    lin_w0,
    lin_x1_slider,
    make_subplots,
    np,
    sympy,
    x,
):
    _L_val = lin_length_slider.value
    _w0_val = lin_load_slider.value
    _x_vals = np.linspace(0, _L_val, 200)

    _m_func = sympy.lambdify(x, lin_m_expr.subs({L: _L_val, lin_w0: _w0_val}), "numpy")
    _v_func = sympy.lambdify(x, lin_v_expr.subs({L: _L_val, lin_w0: _w0_val}), "numpy")
    _m_vals = np.asarray(_m_func(_x_vals), dtype=float)
    _v_vals = np.asarray(_v_func(_x_vals), dtype=float)

    def _rgba(hex_color, alpha):
        hex_color = hex_color.lstrip("#")
        _r, _g, _b = (int(hex_color[i : i + 2], 16) for i in (0, 2, 4))
        return f"rgba({_r}, {_g}, {_b}, {alpha})"

    _m_color = "#4C72B0"
    _v_color = "#C44E52"

    _fig = make_subplots(
        rows=2,
        cols=1,
        shared_xaxes=True,
        subplot_titles=("Bending moment diagram", "Shear force diagram"),
        vertical_spacing=0.12,
    )

    _fig.add_trace(
        go.Scatter(
            x=_x_vals,
            y=_m_vals,
            mode="lines",
            line=dict(color=_m_color, width=2),
            fill="tozeroy",
            fillcolor=_rgba(_m_color, 0.12),
            showlegend=False,
        ),
        row=1,
        col=1,
    )
    _fig.add_trace(
        go.Scatter(
            x=_x_vals,
            y=_v_vals,
            mode="lines",
            line=dict(color=_v_color, width=2),
            fill="tozeroy",
            fillcolor=_rgba(_v_color, 0.12),
            showlegend=False,
        ),
        row=2,
        col=1,
    )

    _x1_val = lin_x1_slider.value
    _m_at_x1 = float(_m_func(_x1_val))
    _v_at_x1 = float(_v_func(_x1_val))

    for _row, _val in ((1, _m_at_x1), (2, _v_at_x1)):
        _fig.add_vline(x=_x1_val, line=dict(color="grey", dash="dash", width=1), row=_row, col=1)
        _fig.add_trace(
            go.Scatter(
                x=[_x1_val],
                y=[_val],
                mode="markers",
                marker=dict(color="black", size=8),
                showlegend=False,
            ),
            row=_row,
            col=1,
        )
        _fig.add_hline(y=0, line=dict(color="black", width=0.8), row=_row, col=1)

    _fig.update_yaxes(title_text="M (kN·m)", autorange="reversed", row=1, col=1)
    _fig.update_yaxes(title_text="V (kN)", row=2, col=1)
    _fig.update_xaxes(title_text="x (m)", row=2, col=1)
    _fig.update_layout(height=600, margin=dict(t=60, b=40), template="plotly_white")

    _fig
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ### Probe the diagrams at a point
    """)
    return


@app.cell
def _(lin_x1_slider):
    lin_x1_slider
    return


@app.cell
def _(Eq, Quantity, Symbol, lin_inputs, lin_m_of_x, lin_v_of_x, lin_x1_slider, mo, pint, x):
    lin_probe_inputs = lin_inputs | {x: Quantity(lin_x1_slider.value, "m")}
    lin_m_probe_eq = Eq(Symbol("M_{x_1}"), lin_m_of_x)
    lin_v_probe_eq = Eq(Symbol("V_{x_1}"), lin_v_of_x)

    # Exact-zero fallback: symeval issue #5 (M(x_1) at either support).
    try:
        lin_m_probe_result = lin_m_probe_eq.sym_evalf(subs=lin_probe_inputs, output_unit="kN*m")
    except pint.errors.DimensionalityError:
        lin_m_probe_result = lin_m_probe_eq.sym_evalf(subs=lin_probe_inputs)
    try:
        lin_v_probe_result = lin_v_probe_eq.sym_evalf(subs=lin_probe_inputs, output_unit="kN")
    except pint.errors.DimensionalityError:
        lin_v_probe_result = lin_v_probe_eq.sym_evalf(subs=lin_probe_inputs)

    mo.vstack([lin_m_probe_result, lin_v_probe_result], align="start", gap=1)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Partial uniform load

    A beam of length $L$, pinned at both ends, carries a uniform load $w$
    over just part of the span, from $x=a$ to $x=b$. Adjust the length,
    load, and the two patch boundaries below.

    ![Simply supported beam with a partial uniform load](public/simply-supported-beam-distributed-load-partial.png)
    *Schematic: CalcpadCE (MIT License)*
    """)
    return


@app.cell
def _(mo):
    pl_length_slider = mo.ui.slider(
        start=1,
        stop=20,
        step=0.5,
        value=10,
        debounce=True,
        include_input=True,
        label="Beam length L (m)",
    )
    pl_load_slider = mo.ui.slider(
        start=1,
        stop=50,
        step=0.5,
        value=5,
        debounce=True,
        include_input=True,
        label="Patch load w (kN/m)",
    )
    mo.hstack([pl_length_slider, pl_load_slider], align="center", justify="center", gap=2)
    return pl_length_slider, pl_load_slider


@app.cell
def _(pl_length_slider, mo):
    pl_a_slider = mo.ui.slider(
        start=0,
        stop=pl_length_slider.value,
        step=pl_length_slider.value / 100,
        value=pl_length_slider.value * 0.3,
        debounce=True,
        include_input=True,
        label="Patch start a (m)",
    )
    return (pl_a_slider,)


@app.cell
def _(pl_a_slider, pl_length_slider, mo):
    pl_b_slider = mo.ui.slider(
        start=pl_a_slider.value,
        stop=pl_length_slider.value,
        step=max((pl_length_slider.value - pl_a_slider.value) / 100, 0.001),
        value=(pl_a_slider.value + pl_length_slider.value) / 2,
        debounce=True,
        include_input=True,
        label="Patch end b (m)",
    )
    mo.hstack([pl_a_slider, pl_b_slider], align="center", justify="center", gap=2)
    return (pl_b_slider,)


@app.cell
def _(Symbol):
    pl_w = Symbol("w")
    pl_a = Symbol("a")
    pl_b = Symbol("b")
    return pl_a, pl_b, pl_w


@app.cell
def _(L, Quantity, pl_a, pl_a_slider, pl_b, pl_b_slider, pl_length_slider, pl_load_slider, pl_w):
    pl_inputs = {
        L: Quantity(pl_length_slider.value, "m"),
        pl_w: Quantity(pl_load_slider.value, "kN/m"),
        pl_a: Quantity(pl_a_slider.value, "m"),
        pl_b: Quantity(pl_b_slider.value, "m"),
    }
    return (pl_inputs,)


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ### Maximum bending moment and shear force

    Replacing the patch by its resultant $w(b-a)$ acting at its centroid
    $(a+b)/2$ gives the two reactions $R_A$, $R_B$; the larger one is
    $V_{max}$. $M_{max}$ occurs where the shear crosses zero - assumed here
    to fall inside the loaded patch, which holds whenever the patch isn't
    pushed all the way to one end:
    """)
    return


@app.cell
def _(L, pl_a, pl_b, pl_w):
    pl_R_A = pl_w * (pl_b - pl_a) * (2 * L - pl_a - pl_b) / (2 * L)
    pl_R_B = pl_w * (pl_b - pl_a) * (pl_a + pl_b) / (2 * L)
    return pl_R_A, pl_R_B


@app.cell
def _(Eq, Symbol, pl_R_A, pl_R_B):
    # Chained (see CONTEXT.md): named as their own R_A/R_B symbols here and
    # evaluated below, then that *result* - not the long underlying formula -
    # is substituted into M_max/V_max, so those stay short enough to render
    # without overflowing.
    pl_R_A_eq = Eq(Symbol("R_A"), pl_R_A)
    pl_R_B_eq = Eq(Symbol("R_B"), pl_R_B)
    return pl_R_A_eq, pl_R_B_eq


@app.cell
def _(pl_R_A_eq, pl_R_B_eq, pl_inputs, mo, pint):
    # A zero-width patch (a = b) makes both reactions exactly zero: symeval
    # issue #5 again.
    try:
        pl_R_A_result = pl_R_A_eq.sym_evalf(subs=pl_inputs, output_unit="kN")
    except pint.errors.DimensionalityError:
        pl_R_A_result = pl_R_A_eq.sym_evalf(subs=pl_inputs)
    try:
        pl_R_B_result = pl_R_B_eq.sym_evalf(subs=pl_inputs, output_unit="kN")
    except pint.errors.DimensionalityError:
        pl_R_B_result = pl_R_B_eq.sym_evalf(subs=pl_inputs)
    mo.vstack([pl_R_A_result, pl_R_B_result], align="start", gap=1)
    return pl_R_A_result, pl_R_B_result


@app.cell
def _(Eq, Symbol, pl_R_A_result, pl_R_B_result, pl_a, pl_a_slider, pl_b_slider, pl_inputs, pl_length_slider, pl_w):
    _R_A, _R_B = Symbol("R_A"), Symbol("R_B")
    pl_m_max_eq = Eq(Symbol("M_max"), _R_A * pl_a + _R_A**2 / (2 * pl_w))
    # Which reaction is larger is decided on the plain slider floats (same
    # reasoning as the concentrated force/moment sections above).
    _R_A_val = (pl_b_slider.value - pl_a_slider.value) * (2 * pl_length_slider.value - pl_a_slider.value - pl_b_slider.value)
    _R_B_val = (pl_b_slider.value - pl_a_slider.value) * (pl_a_slider.value + pl_b_slider.value)
    pl_v_max_eq = Eq(Symbol("V_max"), _R_A if _R_A_val >= _R_B_val else _R_B)
    pl_max_inputs = pl_inputs | {_R_A: pl_R_A_result.quantity, _R_B: pl_R_B_result.quantity}
    return pl_m_max_eq, pl_max_inputs, pl_v_max_eq


@app.cell
def _(pl_m_max_eq, pl_max_inputs, pl_v_max_eq, mo, pint):
    # A zero-width patch (a = b) makes every reaction, and both maxima,
    # exactly zero: symeval issue #5 again.
    try:
        pl_m_max_result = pl_m_max_eq.sym_evalf(subs=pl_max_inputs, output_unit="kN*m")
    except pint.errors.DimensionalityError:
        pl_m_max_result = pl_m_max_eq.sym_evalf(subs=pl_max_inputs)
    try:
        pl_v_max_result = pl_v_max_eq.sym_evalf(subs=pl_max_inputs, output_unit="kN")
    except pint.errors.DimensionalityError:
        pl_v_max_result = pl_v_max_eq.sym_evalf(subs=pl_max_inputs)
    mo.vstack([pl_m_max_result, pl_v_max_result], align="start", gap=1)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ### Bending moment and shear as functions of position
    """)
    return


@app.cell
def _(L, Piecewise, pl_R_A, pl_a, pl_b, pl_w, x):
    pl_m_of_x_left = pl_R_A * x
    pl_m_of_x_mid = pl_R_A * x - pl_w * (x - pl_a) ** 2 / 2
    pl_m_of_x_right = pl_R_A * x - pl_w * (pl_b - pl_a) * (x - (pl_a + pl_b) / 2)
    pl_v_of_x_left = pl_R_A
    pl_v_of_x_mid = pl_R_A - pl_w * (x - pl_a)
    pl_v_of_x_right = pl_R_A - pl_w * (pl_b - pl_a)

    # A genuine three-segment Piecewise; never fed through sym_evalf/
    # quantity_evalf directly (symeval issue #4 - see the UDL section note).
    pl_m_expr = Piecewise(
        (pl_m_of_x_left, (x >= 0) & (x <= pl_a)),
        (pl_m_of_x_mid, (x > pl_a) & (x <= pl_b)),
        (pl_m_of_x_right, (x > pl_b) & (x <= L)),
    )
    pl_v_expr = Piecewise(
        (pl_v_of_x_left, (x >= 0) & (x <= pl_a)),
        (pl_v_of_x_mid, (x > pl_a) & (x <= pl_b)),
        (pl_v_of_x_right, (x > pl_b) & (x <= L)),
    )
    return (
        pl_m_expr,
        pl_m_of_x_left,
        pl_m_of_x_mid,
        pl_m_of_x_right,
        pl_v_expr,
        pl_v_of_x_left,
        pl_v_of_x_mid,
        pl_v_of_x_right,
    )


@app.cell
def _(Eq, Symbol, pl_m_expr, pl_v_expr, mo, sympy):
    mo.vstack(
        [
            mo.md(rf"$\displaystyle {sympy.latex(Eq(Symbol('M(x)'), pl_m_expr))}$"),
            mo.md(rf"$\displaystyle {sympy.latex(Eq(Symbol('V(x)'), pl_v_expr))}$"),
        ]
    )
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ### Diagrams
    """)
    return


@app.cell
def _(pl_length_slider, mo):
    pl_x1_slider = mo.ui.slider(
        start=0,
        stop=pl_length_slider.value,
        step=pl_length_slider.value / 100,
        value=pl_length_slider.value / 2,
        debounce=True,
        include_input=True,
        label="Probe point x_1 (m)",
    )
    return (pl_x1_slider,)


@app.cell
def _(
    L,
    go,
    make_subplots,
    np,
    pl_a,
    pl_a_slider,
    pl_b,
    pl_b_slider,
    pl_length_slider,
    pl_load_slider,
    pl_m_expr,
    pl_v_expr,
    pl_w,
    pl_x1_slider,
    sympy,
    x,
):
    _L_val = pl_length_slider.value
    _w_val = pl_load_slider.value
    _a_val = pl_a_slider.value
    _b_val = pl_b_slider.value
    _x_vals = np.linspace(0, _L_val, 200)

    _m_func = sympy.lambdify(
        x, pl_m_expr.subs({L: _L_val, pl_w: _w_val, pl_a: _a_val, pl_b: _b_val}), "numpy"
    )
    _v_func = sympy.lambdify(
        x, pl_v_expr.subs({L: _L_val, pl_w: _w_val, pl_a: _a_val, pl_b: _b_val}), "numpy"
    )
    _m_vals = np.asarray(_m_func(_x_vals), dtype=float)
    _v_vals = np.asarray(_v_func(_x_vals), dtype=float)

    def _rgba(hex_color, alpha):
        hex_color = hex_color.lstrip("#")
        _r, _g, _b = (int(hex_color[i : i + 2], 16) for i in (0, 2, 4))
        return f"rgba({_r}, {_g}, {_b}, {alpha})"

    _m_color = "#4C72B0"
    _v_color = "#C44E52"

    _fig = make_subplots(
        rows=2,
        cols=1,
        shared_xaxes=True,
        subplot_titles=("Bending moment diagram", "Shear force diagram"),
        vertical_spacing=0.12,
    )

    _fig.add_trace(
        go.Scatter(
            x=_x_vals,
            y=_m_vals,
            mode="lines",
            line=dict(color=_m_color, width=2),
            fill="tozeroy",
            fillcolor=_rgba(_m_color, 0.12),
            showlegend=False,
        ),
        row=1,
        col=1,
    )
    _fig.add_trace(
        go.Scatter(
            x=_x_vals,
            y=_v_vals,
            mode="lines",
            line=dict(color=_v_color, width=2),
            fill="tozeroy",
            fillcolor=_rgba(_v_color, 0.12),
            showlegend=False,
        ),
        row=2,
        col=1,
    )

    _x1_val = pl_x1_slider.value
    _m_at_x1 = float(_m_func(_x1_val))
    _v_at_x1 = float(_v_func(_x1_val))

    for _row, _val in ((1, _m_at_x1), (2, _v_at_x1)):
        _fig.add_vline(x=_x1_val, line=dict(color="grey", dash="dash", width=1), row=_row, col=1)
        _fig.add_trace(
            go.Scatter(
                x=[_x1_val],
                y=[_val],
                mode="markers",
                marker=dict(color="black", size=8),
                showlegend=False,
            ),
            row=_row,
            col=1,
        )
        _fig.add_hline(y=0, line=dict(color="black", width=0.8), row=_row, col=1)

    _fig.update_yaxes(title_text="M (kN·m)", autorange="reversed", row=1, col=1)
    _fig.update_yaxes(title_text="V (kN)", row=2, col=1)
    _fig.update_xaxes(title_text="x (m)", row=2, col=1)
    _fig.update_layout(height=600, margin=dict(t=60, b=40), template="plotly_white")

    _fig
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ### Probe the diagrams at a point
    """)
    return


@app.cell
def _(pl_x1_slider):
    pl_x1_slider
    return


@app.cell
def _(
    Eq,
    Quantity,
    Symbol,
    pl_a,
    pl_a_slider,
    pl_b,
    pl_b_slider,
    pl_inputs,
    pl_m_of_x_left,
    pl_m_of_x_mid,
    pl_m_of_x_right,
    pl_v_of_x_left,
    pl_v_of_x_mid,
    pl_v_of_x_right,
    pl_x1_slider,
    mo,
    pint,
    x,
):
    pl_probe_inputs = pl_inputs | {x: Quantity(pl_x1_slider.value, "m")}

    if pl_x1_slider.value <= pl_a_slider.value:
        pl_m_branch, pl_v_branch = pl_m_of_x_left, pl_v_of_x_left
    elif pl_x1_slider.value <= pl_b_slider.value:
        pl_m_branch, pl_v_branch = pl_m_of_x_mid, pl_v_of_x_mid
    else:
        pl_m_branch, pl_v_branch = pl_m_of_x_right, pl_v_of_x_right

    pl_m_probe_eq = Eq(Symbol("M_{x_1}"), pl_m_branch)
    pl_v_probe_eq = Eq(Symbol("V_{x_1}"), pl_v_branch)

    try:
        pl_m_probe_result = pl_m_probe_eq.sym_evalf(subs=pl_probe_inputs, output_unit="kN*m")
    except pint.errors.DimensionalityError:
        pl_m_probe_result = pl_m_probe_eq.sym_evalf(subs=pl_probe_inputs)
    try:
        pl_v_probe_result = pl_v_probe_eq.sym_evalf(subs=pl_probe_inputs, output_unit="kN")
    except pint.errors.DimensionalityError:
        pl_v_probe_result = pl_v_probe_eq.sym_evalf(subs=pl_probe_inputs)

    mo.vstack([pl_m_probe_result, pl_v_probe_result], align="start", gap=1)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Concentrated forces

    A beam of length $L$, pinned at both ends, carries two point loads:
    $P_1$ at a distance $a_1$ from the left support, and $P_2$ at a
    distance $a_2 \geq a_1$. Adjust the length and the two loads/positions
    below.

    ![Simply supported beam with two concentrated forces](public/simply-supported-beam-forces.png)
    *Schematic: CalcpadCE (MIT License)*
    """)
    return


@app.cell
def _(mo):
    cfs_length_slider = mo.ui.slider(
        start=1,
        stop=20,
        step=0.5,
        value=10,
        debounce=True,
        include_input=True,
        label="Beam length L (m)",
    )
    cfs_length_slider
    return (cfs_length_slider,)


@app.cell
def _(cfs_length_slider, mo):
    cfs_p1_slider = mo.ui.slider(
        start=1,
        stop=200,
        step=1,
        value=30,
        debounce=True,
        include_input=True,
        label="Load P_1 (kN)",
    )
    cfs_a1_slider = mo.ui.slider(
        start=0,
        stop=cfs_length_slider.value,
        step=cfs_length_slider.value / 100,
        value=cfs_length_slider.value * 0.3,
        debounce=True,
        include_input=True,
        label="Position a_1 (m)",
    )
    mo.hstack([cfs_p1_slider, cfs_a1_slider], align="center", justify="center", gap=2)
    return cfs_a1_slider, cfs_p1_slider


@app.cell
def _(cfs_a1_slider, cfs_length_slider, mo):
    cfs_p2_slider = mo.ui.slider(
        start=1,
        stop=200,
        step=1,
        value=40,
        debounce=True,
        include_input=True,
        label="Load P_2 (kN)",
    )
    cfs_a2_slider = mo.ui.slider(
        start=cfs_a1_slider.value,
        stop=cfs_length_slider.value,
        step=max((cfs_length_slider.value - cfs_a1_slider.value) / 100, 0.001),
        value=(cfs_a1_slider.value + cfs_length_slider.value) / 2,
        debounce=True,
        include_input=True,
        label="Position a_2 (m)",
    )
    mo.hstack([cfs_p2_slider, cfs_a2_slider], align="center", justify="center", gap=2)
    return cfs_a2_slider, cfs_p2_slider


@app.cell
def _(Symbol):
    cfs_P1 = Symbol("P_1")
    cfs_a1 = Symbol("a_1")
    cfs_P2 = Symbol("P_2")
    cfs_a2 = Symbol("a_2")
    return cfs_P1, cfs_P2, cfs_a1, cfs_a2


@app.cell
def _(
    L,
    Quantity,
    cfs_P1,
    cfs_P2,
    cfs_a1,
    cfs_a1_slider,
    cfs_a2,
    cfs_a2_slider,
    cfs_length_slider,
    cfs_p1_slider,
    cfs_p2_slider,
):
    cfs_inputs = {
        L: Quantity(cfs_length_slider.value, "m"),
        cfs_P1: Quantity(cfs_p1_slider.value, "kN"),
        cfs_a1: Quantity(cfs_a1_slider.value, "m"),
        cfs_P2: Quantity(cfs_p2_slider.value, "kN"),
        cfs_a2: Quantity(cfs_a2_slider.value, "m"),
    }
    return (cfs_inputs,)


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ### Maximum bending moment and shear force

    The moment diagram is piecewise-linear with corners under each load, so
    $M_{max}$ is the larger of the two corner values, $M(a_1)$ and
    $M(a_2)$. The shear is piecewise-constant, so $V_{max}$ is the largest
    of its three segment values:
    """)
    return


@app.cell
def _(L, cfs_P1, cfs_P2, cfs_a1, cfs_a2):
    cfs_R_A = (cfs_P1 * (L - cfs_a1) + cfs_P2 * (L - cfs_a2)) / L
    cfs_R_B = (cfs_P1 * cfs_a1 + cfs_P2 * cfs_a2) / L
    return cfs_R_A, cfs_R_B


@app.cell
def _(
    Eq,
    Symbol,
    cfs_P1,
    cfs_R_A,
    cfs_R_B,
    cfs_a1,
    cfs_a1_slider,
    cfs_a2,
    cfs_a2_slider,
    cfs_length_slider,
    cfs_p1_slider,
    cfs_p2_slider,
):
    _L_val = cfs_length_slider.value
    _P1_val = cfs_p1_slider.value
    _a1_val = cfs_a1_slider.value
    _P2_val = cfs_p2_slider.value
    _a2_val = cfs_a2_slider.value
    _R_A_val = (_P1_val * (_L_val - _a1_val) + _P2_val * (_L_val - _a2_val)) / _L_val
    _R_B_val = (_P1_val * _a1_val + _P2_val * _a2_val) / _L_val

    # M(a1) vs M(a2), decided on the plain slider floats (same reasoning as
    # every branch pick in the sections above).
    _m_a1_val = _R_A_val * _a1_val
    _m_a2_val = _R_A_val * _a2_val - _P1_val * (_a2_val - _a1_val)
    if abs(_m_a1_val) >= abs(_m_a2_val):
        cfs_m_max_eq = Eq(Symbol("M_max"), cfs_R_A * cfs_a1)
    else:
        cfs_m_max_eq = Eq(Symbol("M_max"), cfs_R_A * cfs_a2 - cfs_P1 * (cfs_a2 - cfs_a1))

    # Largest of the three constant shear segments: R_A, R_A - P1, -R_B.
    _v_mid_val = _R_A_val - _P1_val
    _candidates = [(abs(_R_A_val), cfs_R_A), (abs(_v_mid_val), cfs_R_A - cfs_P1), (abs(_R_B_val), cfs_R_B)]
    _, _v_max_expr = max(_candidates, key=lambda pair: pair[0])
    cfs_v_max_eq = Eq(Symbol("V_max"), _v_max_expr)
    return cfs_m_max_eq, cfs_v_max_eq


@app.cell
def _(cfs_inputs, cfs_m_max_eq, cfs_v_max_eq, mo, pint):
    # Exact-zero fallback: symeval issue #5 (e.g. a1 = 0, or a cancelling shear).
    try:
        cfs_m_max_result = cfs_m_max_eq.sym_evalf(subs=cfs_inputs, output_unit="kN*m")
    except pint.errors.DimensionalityError:
        cfs_m_max_result = cfs_m_max_eq.sym_evalf(subs=cfs_inputs)
    try:
        cfs_v_max_result = cfs_v_max_eq.sym_evalf(subs=cfs_inputs, output_unit="kN")
    except pint.errors.DimensionalityError:
        cfs_v_max_result = cfs_v_max_eq.sym_evalf(subs=cfs_inputs)
    mo.vstack([cfs_m_max_result, cfs_v_max_result], align="start", gap=1)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ### Bending moment and shear as functions of position
    """)
    return


@app.cell
def _(L, Piecewise, cfs_P1, cfs_P2, cfs_R_A, cfs_a1, cfs_a2, x):
    cfs_m_of_x_left = cfs_R_A * x
    cfs_m_of_x_mid = cfs_R_A * x - cfs_P1 * (x - cfs_a1)
    cfs_m_of_x_right = cfs_R_A * x - cfs_P1 * (x - cfs_a1) - cfs_P2 * (x - cfs_a2)
    cfs_v_of_x_left = cfs_R_A
    cfs_v_of_x_mid = cfs_R_A - cfs_P1
    cfs_v_of_x_right = cfs_R_A - cfs_P1 - cfs_P2

    cfs_m_expr = Piecewise(
        (cfs_m_of_x_left, (x >= 0) & (x <= cfs_a1)),
        (cfs_m_of_x_mid, (x > cfs_a1) & (x <= cfs_a2)),
        (cfs_m_of_x_right, (x > cfs_a2) & (x <= L)),
    )
    cfs_v_expr = Piecewise(
        (cfs_v_of_x_left, (x >= 0) & (x <= cfs_a1)),
        (cfs_v_of_x_mid, (x > cfs_a1) & (x <= cfs_a2)),
        (cfs_v_of_x_right, (x > cfs_a2) & (x <= L)),
    )
    return (
        cfs_m_expr,
        cfs_m_of_x_left,
        cfs_m_of_x_mid,
        cfs_m_of_x_right,
        cfs_v_expr,
        cfs_v_of_x_left,
        cfs_v_of_x_mid,
        cfs_v_of_x_right,
    )


@app.cell
def _(Eq, Symbol, cfs_m_expr, cfs_v_expr, mo, sympy):
    mo.vstack(
        [
            mo.md(rf"$\displaystyle {sympy.latex(Eq(Symbol('M(x)'), cfs_m_expr))}$"),
            mo.md(rf"$\displaystyle {sympy.latex(Eq(Symbol('V(x)'), cfs_v_expr))}$"),
        ]
    )
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ### Diagrams
    """)
    return


@app.cell
def _(cfs_length_slider, mo):
    cfs_x1_slider = mo.ui.slider(
        start=0,
        stop=cfs_length_slider.value,
        step=cfs_length_slider.value / 100,
        value=cfs_length_slider.value / 2,
        debounce=True,
        include_input=True,
        label="Probe point x_1 (m)",
    )
    return (cfs_x1_slider,)


@app.cell
def _(
    L,
    cfs_P1,
    cfs_P2,
    cfs_a1,
    cfs_a1_slider,
    cfs_a2,
    cfs_a2_slider,
    cfs_length_slider,
    cfs_m_expr,
    cfs_p1_slider,
    cfs_p2_slider,
    cfs_v_expr,
    cfs_x1_slider,
    go,
    make_subplots,
    np,
    sympy,
    x,
):
    _L_val = cfs_length_slider.value
    _P1_val = cfs_p1_slider.value
    _a1_val = cfs_a1_slider.value
    _P2_val = cfs_p2_slider.value
    _a2_val = cfs_a2_slider.value
    _x_vals = np.linspace(0, _L_val, 200)

    _subs_map = {L: _L_val, cfs_P1: _P1_val, cfs_a1: _a1_val, cfs_P2: _P2_val, cfs_a2: _a2_val}
    _m_func = sympy.lambdify(x, cfs_m_expr.subs(_subs_map), "numpy")
    _v_func = sympy.lambdify(x, cfs_v_expr.subs(_subs_map), "numpy")
    _m_vals = np.asarray(_m_func(_x_vals), dtype=float)
    _v_vals = np.asarray(_v_func(_x_vals), dtype=float)

    def _rgba(hex_color, alpha):
        hex_color = hex_color.lstrip("#")
        _r, _g, _b = (int(hex_color[i : i + 2], 16) for i in (0, 2, 4))
        return f"rgba({_r}, {_g}, {_b}, {alpha})"

    _m_color = "#4C72B0"
    _v_color = "#C44E52"

    _fig = make_subplots(
        rows=2,
        cols=1,
        shared_xaxes=True,
        subplot_titles=("Bending moment diagram", "Shear force diagram"),
        vertical_spacing=0.12,
    )

    _fig.add_trace(
        go.Scatter(
            x=_x_vals,
            y=_m_vals,
            mode="lines",
            line=dict(color=_m_color, width=2),
            fill="tozeroy",
            fillcolor=_rgba(_m_color, 0.12),
            showlegend=False,
        ),
        row=1,
        col=1,
    )
    _fig.add_trace(
        go.Scatter(
            x=_x_vals,
            y=_v_vals,
            mode="lines",
            line=dict(color=_v_color, width=2),
            fill="tozeroy",
            fillcolor=_rgba(_v_color, 0.12),
            showlegend=False,
        ),
        row=2,
        col=1,
    )

    _x1_val = cfs_x1_slider.value
    _m_at_x1 = float(_m_func(_x1_val))
    _v_at_x1 = float(_v_func(_x1_val))

    for _row, _val in ((1, _m_at_x1), (2, _v_at_x1)):
        _fig.add_vline(x=_x1_val, line=dict(color="grey", dash="dash", width=1), row=_row, col=1)
        _fig.add_trace(
            go.Scatter(
                x=[_x1_val],
                y=[_val],
                mode="markers",
                marker=dict(color="black", size=8),
                showlegend=False,
            ),
            row=_row,
            col=1,
        )
        _fig.add_hline(y=0, line=dict(color="black", width=0.8), row=_row, col=1)

    _fig.update_yaxes(title_text="M (kN·m)", autorange="reversed", row=1, col=1)
    _fig.update_yaxes(title_text="V (kN)", row=2, col=1)
    _fig.update_xaxes(title_text="x (m)", row=2, col=1)
    _fig.update_layout(height=600, margin=dict(t=60, b=40), template="plotly_white")

    _fig
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ### Probe the diagrams at a point
    """)
    return


@app.cell
def _(cfs_x1_slider):
    cfs_x1_slider
    return


@app.cell
def _(
    Eq,
    Quantity,
    Symbol,
    cfs_a1_slider,
    cfs_a2_slider,
    cfs_inputs,
    cfs_m_of_x_left,
    cfs_m_of_x_mid,
    cfs_m_of_x_right,
    cfs_v_of_x_left,
    cfs_v_of_x_mid,
    cfs_v_of_x_right,
    cfs_x1_slider,
    mo,
    pint,
    x,
):
    cfs_probe_inputs = cfs_inputs | {x: Quantity(cfs_x1_slider.value, "m")}

    if cfs_x1_slider.value <= cfs_a1_slider.value:
        cfs_m_branch, cfs_v_branch = cfs_m_of_x_left, cfs_v_of_x_left
    elif cfs_x1_slider.value <= cfs_a2_slider.value:
        cfs_m_branch, cfs_v_branch = cfs_m_of_x_mid, cfs_v_of_x_mid
    else:
        cfs_m_branch, cfs_v_branch = cfs_m_of_x_right, cfs_v_of_x_right

    cfs_m_probe_eq = Eq(Symbol("M_{x_1}"), cfs_m_branch)
    cfs_v_probe_eq = Eq(Symbol("V_{x_1}"), cfs_v_branch)

    try:
        cfs_m_probe_result = cfs_m_probe_eq.sym_evalf(subs=cfs_probe_inputs, output_unit="kN*m")
    except pint.errors.DimensionalityError:
        cfs_m_probe_result = cfs_m_probe_eq.sym_evalf(subs=cfs_probe_inputs)
    try:
        cfs_v_probe_result = cfs_v_probe_eq.sym_evalf(subs=cfs_probe_inputs, output_unit="kN")
    except pint.errors.DimensionalityError:
        cfs_v_probe_result = cfs_v_probe_eq.sym_evalf(subs=cfs_probe_inputs)

    mo.vstack([cfs_m_probe_result, cfs_v_probe_result], align="start", gap=1)
    return


if __name__ == "__main__":
    app.run()
