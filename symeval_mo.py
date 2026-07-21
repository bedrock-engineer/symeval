# /// script
# requires-python = ">=3.12"
# dependencies = [
#     "marimo",
#     "pint",
#     "polars",
#     "pytest",
#     "sympy",
# ]
# ///

import marimo

__generated_with = "0.23.14"
app = marimo.App(width="columns")

with app.setup(hide_code=True):
    ## EXPORT

    from dataclasses import dataclass
    from typing import Literal

    import pint
    import sympy


    def _quantity_to_sympy_base(quantity: pint.Quantity) -> sympy.Expr:
        """Convert a pint quantity to a sympy expression in base SI units.

        Dimensionless quantities return their bare magnitude (a Python float).
        """
        if quantity.dimensionality == {}:
            return quantity.magnitude
        base = quantity.to_base_units()
        sympy_units = sympy.sympify(f"{base.units:~D}")
        return base.magnitude * sympy_units

    def _resolve_formula(
        formula: "sympy.Expr | sympy.Equality",
        subs: dict,
    ) -> "tuple[sympy.Expr, sympy.Symbol | None]":
        """Resolve a *formula* (expression or equation) into `(expression, output_symbol)`.

        A bare `sympy.Expr` passes through unchanged, with `None` for the output
        symbol (the caller must supply `output_symbol` itself).

        A `sympy.Equality` is solved for its single unknown, the one free symbol that
        has no value in `subs` (everything in `subs` is a known input). When that
        unknown is already isolated on one side of the equation, the other side is
        returned verbatim so the rendered formula keeps the shape the user wrote;
        otherwise `sympy.solve` isolates it.

        Raises:
            ValueError: If the equation does not have exactly one unknown, or if
                solving it does not yield a unique solution.
        """
        if not isinstance(formula, sympy.Equality):
            return formula, None
        unknowns = formula.free_symbols - set(subs)
        if len(unknowns) != 1:
            raise ValueError(
                "Expected exactly one unknown: a free symbol of the equation with "
                "no value in `subs`. Found "
                f"{sorted(map(str, unknowns))}. Provide `subs` values for every "
                "symbol except the one to solve for."
            )
        (unknown,) = unknowns
        if formula.lhs == unknown:
            return formula.rhs, unknown
        if formula.rhs == unknown:
            return formula.lhs, unknown
        solutions = sympy.solve(formula, unknown)
        if len(solutions) != 1:
            raise ValueError(
                f"Solving for {unknown} gave {len(solutions)} solutions "
                f"({solutions}); SymEval needs a unique one. Solve the equation "
                "yourself and pass the branch you want."
            )
        return solutions[0], unknown

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
        `expr.evalf(...)`, so `n`, `maxn`, `chop`, `strict`, `quiet`, and
        `verbose` all work without being listed here individually.

        Args:
            expr (sympy.Expr): The sympy expression to evaluate. Equations are
                not accepted here; use `sym_evalf` for a `sympy.Equality`, or solve
                it first and pass the resulting expression.
            subs (dict[sympy.Symbol, pint.Quantity] | None): Mapping from
                `sympy.Symbol` to `pint.Quantity` (a dimensionless input is still a quantity, `Quantity(x, "")`). Same shape as sympy.evalf's `subs` kwarg, but values
                carry units. Defaults to None (no substitutions).
            output_unit (str | pint.Unit | None): Target pint unit for the
                result (e.g. `"MPa"` or `ureg.MPa`). If `None`, the result is
                returned in SI base units. Defaults to None. The result's
                registry is the registry of the input `pint.Quantity` values
                in `subs`; with empty subs,
                `pint.get_application_registry()` is used as a fallback.
            **evalf_kwargs: Forwarded verbatim to `expr.evalf(...)`. Useful
                kwargs include `n` (digits of precision), `chop` (round tiny
                terms to zero), and `strict` (raise instead of returning an
                unevaluated result).

        Returns:
            pint.Quantity: The computed quantity, in `output_unit` if given,
                else in SI base units.
        """
        subs = subs or {}
        if isinstance(expr, sympy.Equality):
            raise TypeError(
                "quantity_evalf evaluates a bare expression, not an equation. "
                "Use sym_evalf for a sympy.Equality (it infers the output symbol), or "
                "solve first: sympy.solve(eq, unknown)[0].quantity_evalf(...)."
            )
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

        `kg` is left as-is because it is itself the SI base unit for mass, even
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

    def _format_quantity(
        quantity: pint.Quantity,
        places: int,
        *,
        scientific: bool,
        trim: bool,
    ) -> str:
        """Format a pint quantity as a LaTeX `magnitude + unit` string.

        `places` sets the decimal places; `scientific` picks `.Ne` over `.Nf`;
        `trim` drops trailing zeros (and a dangling decimal point) from the
        magnitude, so a clean value like 500 renders as `500`, not `500.000`.

        Rendering at a fixed number of places also rounds away pint's float-based
        conversion noise (100 mm^2 becomes 1e-4 m^2, not 9.999e-5).
        """
        spec = f".{places}e~L" if scientific else f".{places}f~L"
        formatted = f"{quantity:{spec}}"
        if not trim:
            return formatted
        mag_str, sep, unit_str = formatted.partition("\\ ")
        if "." in mag_str:
            mag_str = mag_str.rstrip("0").rstrip(".")
        return f"{mag_str}{sep}{unit_str}"

    def _si_stripped(quantity: pint.Quantity) -> "tuple[pint.Quantity, bool]":
        """Return `(quantity in SI-prefix-free units, whether that changed the unit)`.

        The flag drives the scientific-notation choice: a unit that carried an SI
        prefix (kN, mm, MPa) reads better in scientific form once stripped to its
        base unit. Centralised here so the substituted SI line and the result-line
        dual ask the question in one place.
        """
        stripped = _strip_si_prefixes(quantity)
        return stripped, stripped.units != quantity.units

    def _format_substituted_value(
        quantity: pint.Quantity,
        decimals: int,
        *,
        si_stripped: bool = False,
    ) -> str:
        """Format one input value for the substituted form.

        Substituted inputs show one more place than the result (`decimals + 1`),
        trailing zeros trimmed. With `si_stripped` True the value is shown in SI
        base units, in scientific notation when stripping changed the unit.
        """
        if si_stripped:
            shown, scientific = _si_stripped(quantity)
        else:
            shown, scientific = quantity, False
        return _format_quantity(
            shown, decimals + 1, scientific=scientific, trim=not scientific
        )

    def _format_result(
        quantity: pint.Quantity,
        decimals: int,
    ) -> "tuple[str, str]":
        """Format the result line, returning `(value_latex, dual_latex)`.

        `value_latex` is the quantity at exactly `decimals` places in its own unit.
        `dual_latex` prepends a prefix-stripped scientific form (`sci = value`) when
        the unit carries an SI prefix, otherwise it equals `value_latex`.
        """
        value_latex = _format_quantity(quantity, decimals, scientific=False, trim=False)
        stripped, changed = _si_stripped(quantity)
        if changed:
            sci = _format_quantity(stripped, decimals, scientific=True, trim=False)
            return value_latex, f"{sci} = {value_latex}"
        return value_latex, value_latex

    def _render_substituted(
        expr: sympy.Expr,
        subs: dict[sympy.Symbol, pint.Quantity],
        decimals: int,
        *,
        si_stripped: bool = False,
    ) -> str:
        """Render the substituted form: `expr` with each input symbol replaced by its formatted value and unit.

        The placeholder trick lives here, in one place. Each input symbol is
        swapped for a unique `SymEvalPH#Z` symbol so sympy renders the structure
        without simplifying (``a + a`` stays ``a + a``) or dropping units; each
        placeholder is then spliced back to a formatted `value + unit` string. The
        trailing "Z" keeps the substring replace safe: `SymEvalPH0Z` never matches
        inside `SymEvalPH10Z`. Placeholder indices follow the canonical sort order
        of the input symbols, so sympy.Mul ordering matches the symbolic form.

        With `si_stripped` True, each quantity is converted to its SI-prefix-free
        form (kN -> N, mm -> m) and shown in scientific notation when that
        conversion changed its unit; this is the extra line rendered in verbose
        mode.

        A value carrying a unit is wrapped in ``\\left(...\\right)`` when it sits
        under an exponent, so the power binds to the whole quantity, not the unit.
        """
        input_symbols = list(subs.keys())
        input_quantities = list(subs.values())

        canonical_order = sorted(
            range(len(input_symbols)), key=lambda i: input_symbols[i].sort_key()
        )
        placeholder_syms = [None] * len(input_symbols)
        for canonical_pos, orig_idx in enumerate(canonical_order):
            placeholder_syms[orig_idx] = sympy.Symbol(f"SymEvalPH{canonical_pos}Z")
        sub_map = dict(zip(input_symbols, placeholder_syms))
        rendered = sympy.latex(expr.subs(sub_map, simultaneous=True))

        for quantity, placeholder in zip(input_quantities, placeholder_syms):
            formatted = _format_substituted_value(
                quantity, decimals, si_stripped=si_stripped
            )
            ph_latex = sympy.latex(placeholder)
            if not quantity.dimensionless:
                wrapped = rf"\medspace\left({formatted}\right)"
                rendered = rendered.replace(f"{ph_latex}^", f"{wrapped}^")
            rendered = rendered.replace(ph_latex, rf"\medspace{formatted}")
        return rendered

    @dataclass
    class _Working:
        """The pieces of one symbolic evaluation's working, before layout.

        `symbol` is the output label; `symbolic` the formula with symbols;
        `substituted` the formula with numbers. `result_value` is the result in its
        own unit and `result_dual` the same with a prefix-stripped scientific dual
        (equal to `result_value` when the unit carries no SI prefix). `si_substituted`
        is the extra SI-base line, present only in verbose mode.
        """

        symbol: str
        symbolic: str
        substituted: str
        result_value: str
        result_dual: str
        si_substituted: "str | None" = None

    def _layout_one_line(working: _Working) -> str:
        """Arrange a working on one line: symbol = formula = numbers = result."""
        return (
            f"{working.symbol} = {working.symbolic}"
            f" = {working.substituted} = {working.result_value}"
        )

    def _layout_align(working: _Working) -> str:
        """Arrange a working as a stacked LaTeX `align*` block.

        Includes the SI-base substituted line when the working carries one (verbose).
        """
        lines = [
            rf"{working.symbol} &= {working.symbolic} \\",
            rf"&= {working.substituted} \\",
        ]
        if working.si_substituted is not None:
            lines.append(rf"&= {working.si_substituted} \\")
        lines.append(rf"{working.symbol} &= {working.result_dual}")
        return "\\begin{align*}\n" + "\n".join(lines) + "\n\\end{align*}"

    # The one place a mode is defined: its layout, and whether it carries the SI line.
    # Adding a mode is one entry here (plus a layout function if the arrangement is new).
    _MODES = {
        "one_line": (_layout_one_line, False),
        "multi_line": (_layout_align, False),
        "verbose": (_layout_align, True),
    }

    class SymbolicEvaluation:
        """A pint Quantity wrapper with an attached LaTeX rendering for marimo/Jupyter.

        Returned by `sym_evalf`. Transparent wrapper around `self.quantity`: any
        attribute or method not defined here (magnitude, units, to, to_reduced_units,
        m_as, ...) is delegated to the quantity through `__getattr__`. This class defines no
        arithmetic or comparison operators; do math on `.quantity`. (Because the
        delegated magnitude/units make the wrapper quack like a Quantity, pint may
        still duck-type it in arithmetic and hand back a plain Quantity, which is
        fine.) What this class adds: `.latex` (the rendered LaTeX), `.symbol`
        (the output sympy.Symbol), and `_repr_latex_`.

        `.symbol` is the output sympy.Symbol: reference it when building a later
        equation and pair it with `.quantity` in that evaluation's `subs` to chain
        calculations.
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

        def __getattr__(self, name: str):
            # Guard `quantity` so a half-built instance raises cleanly instead of
            # recursing. (__getattr__ runs only when normal attribute lookup fails.)
            if name == "quantity":
                raise AttributeError(name)
            return getattr(self.quantity, name)

        def _repr_latex_(self) -> str:
            return f"$$ {self.latex} $$"

        def __repr__(self):
            return f"SymbolicEvaluation({self.quantity!r})"

        def __str__(self):
            return str(self.quantity)

    def sym_evalf(
        expr: "sympy.Expr | sympy.Equality",
        *,
        subs: dict[sympy.Symbol, pint.Quantity] | None = None,
        output_symbol: str | sympy.Symbol | None = None,
        output_unit: str | pint.Unit | None = None,
        decimals: int = 3,
        mode: Literal["multi_line", "verbose", "one_line"] = "multi_line",
        **evalf_kwargs,
    ) -> "SymbolicEvaluation":
        """Numerically evaluate `expr` and render it as LaTeX.

        Same numeric kernel as `quantity_evalf`; the addition is the LaTeX
        rendering attached to the returned `SymbolicEvaluation`.

        Args:
            expr (sympy.Expr | sympy.Equality): The expression to evaluate,
                or a `sympy.Eq` whose single unknown (the free symbol absent from
                `subs`) is solved for. For an equation the output symbol is
                inferred, so `output_symbol` may be omitted.
            subs (dict[sympy.Symbol, pint.Quantity] | None): Mapping from
                `sympy.Symbol` to `pint.Quantity` (a dimensionless input is still a quantity, `Quantity(x, "")`). Same shape as sympy.evalf's `subs` kwarg. Defaults to
                None (no substitutions).
            output_symbol (str | sympy.Symbol | None): LaTeX label for the
                output: a string like `r"\\sigma"` or a `sympy.Symbol`. The label
                appears on the left of every line of the rendering.
                Keyword-only. Required for a bare expression; for an equation it
                defaults to the inferred unknown, and an explicit value overrides
                only the rendered label.
            output_unit (str | pint.Unit | None): Target pint unit for the
                result. If `None`, the result is rendered in SI base units.
                Defaults to None.
            decimals (int): Decimal places for the result; substituted inputs
                show one more place, with trailing zeros trimmed. Defaults to 3.
            mode (Literal["multi_line", "verbose", "one_line"]): Rendering
                style, defaults to `"multi_line"`:

                - `"multi_line"`: three lines: symbolic form, substituted form with
                  units, then result.
                - `"verbose"`: four lines: multi_line plus an extra
                  substituted form in SI base units, in scientific notation.
                - `"one_line"`: a single line,
                  `symbol = symbolic form = substituted form = result`, with just the
                  variable's unit on the right (no prefix-stripped dual).
            **evalf_kwargs: Forwarded to `expr.evalf(...)` via
                `quantity_evalf`. Useful kwargs: `n` (digits of precision),
                `chop`, `strict`.

        Returns:
            SymbolicEvaluation: The computed `pint.Quantity` with the rendered
                LaTeX rendering attached. Renders in marimo / Jupyter via
                `_repr_latex_`. Has `.quantity`, `.latex`, and `.symbol` for
                chaining into downstream sympy expressions.

        Raises:
            ValueError: If `output_symbol` is omitted for a bare expression; if
                an equation has zero or more than one unknown (a free symbol
                absent from `subs`); if solving the equation yields no unique
                solution; or if `mode` is not one of the allowed values.
        """
        if mode not in _MODES:
            raise ValueError(f"mode must be one of {tuple(_MODES)}, got {mode!r}")
        layout, wants_si = _MODES[mode]
        subs = subs or {}
        expr, _inferred_symbol = _resolve_formula(expr, subs)
        if output_symbol is None:
            if _inferred_symbol is None:
                raise ValueError(
                    "output_symbol is required when evaluating a bare sympy "
                    "expression. Pass a sympy.Equality instead and the output symbol "
                    "is inferred from the equation."
                )
            output_symbol = _inferred_symbol

        expression_latex = sympy.latex(expr)

        substituted_latex = _render_substituted(expr, subs, decimals)

        si_substituted_latex = (
            _render_substituted(expr, subs, decimals, si_stripped=True)
            if wants_si
            else None
        )

        output_quantity = quantity_evalf(
            expr, subs=subs, output_unit=output_unit, **evalf_kwargs
        )

        output_var_unit_latex, output_dual_latex = _format_result(
            output_quantity, decimals
        )

        if isinstance(output_symbol, sympy.Symbol):
            output_sym = output_symbol
        else:
            output_sym = sympy.Symbol(str(output_symbol))
        sym_latex = sympy.latex(output_sym)
        # `full_latex` is the BARE LaTeX (no `$` delimiters). SymbolicEvaluation._repr_latex_
        # adds `$$...$$` for the default display rendering. Callers embedding the
        # math elsewhere wrap explicitly via `result.latex` (`${...}$` for inline,
        # `$${...}$$` for display).
        working = _Working(
            symbol=sym_latex,
            symbolic=expression_latex,
            substituted=substituted_latex,
            result_value=output_var_unit_latex,
            result_dual=output_dual_latex,
            si_substituted=si_substituted_latex,
        )
        full_latex = layout(working)

        return SymbolicEvaluation(output_quantity, full_latex, output_sym)

    # Method bindings so users can write `expr.sym_evalf(...)`,
    # `equation.sym_evalf(...)`, or `expr.quantity_evalf(...)`.
    #
    # sym_evalf accepts an equation (it infers the output symbol from the
    # equation), so it's bound on Equality as well as Expr, mirroring how
    # sympy's own `.subs`/`.evalf` live on Basic and work on both. quantity_evalf
    # is the bare-value fast path (no label to infer) and stays expression-only,
    # so it's bound on Expr alone. Bind the functions directly (not via lambdas)
    # so introspection tools (`help`, marimo's 'View live docs', IDE hovers)
    # see the real signature and docstring rather than a generic `lambda(**kw)`.
    sympy.Expr.quantity_evalf = quantity_evalf
    sympy.Expr.sym_evalf = sym_evalf
    sympy.Equality.sym_evalf = sym_evalf


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    The implementation of SymEval lives in the [setup cell](https://docs.marimo.io/guides/reusing_functions/#1-create-a-setup-cell), and gets exported to `./src/symeval/__init__.py` by [`mobuild`](https://github.com/koaning/mobuild), because it's marked with `## EXPORT`.

    I preferred putting the implementation into the setup cell so it runs first. The examples call .sym_evalf, which is monkey-patched onto sympy.Equality, so marimo's dependency graph can't see that they need the implementation. The setup cell guarantees the right order anyway.
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    # Getting started with SymEval

    SymEval allows you to define [SymPy](https://docs.sympy.org/latest/index.html) equations, then substitute [Pint](https://pint.readthedocs.io/en/stable/) quantities (value + unit), and then shows symbolically (LaTeX) you how to arrive at the result.

    Below some examples that start with the basics and progressively show more powerful SymEval funcionality and usecases.

    ## Axial stress under a compressive force
    """)
    return


@app.cell
def _():
    import marimo as mo
    import polars as pl
    # import sympy

    from pint import Quantity
    # from symeval import quantity_evalf, sym_evalf
    from sympy import Equality, Symbol

    return Equality, Quantity, Symbol, mo, pl


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    Define the equation for calculating the axial stress using SymPy:
    """)
    return


@app.cell
def _(Equality, Symbol):
    axial_stress_eq = Equality(Symbol(r"\sigma"), Symbol("F") / Symbol("A"))
    axial_stress_eq
    return (axial_stress_eq,)


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    Then define the values and units of the force acting on the structural member and its cross-sectional area:
    """)
    return


@app.cell
def _(Quantity, Symbol):
    fa_inputs = {
        Symbol("F"): Quantity(-680, "kN"),
        Symbol("A"): Quantity(10_580, "mm^2"),
    }
    fa_inputs
    return (fa_inputs,)


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    Then substitute the inputs into the SymPy equation:
    """)
    return


@app.cell
def _(axial_stress_eq, fa_inputs):
    axial_stress = sym_evalf(
        axial_stress_eq,
        subs=fa_inputs,
        output_unit="MPa",
    )
    axial_stress
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    For convenience, it's also possible to call `sym_evalf` as a metod on a `sympy.Equality`. Moreover, there are a few keyword arguments (kwargs) to help you nicely format the LaTeX:

    - `decimals` specifies the number of decimals used in LaTeX.
    - `mode="verbose"` adds an extra line showing all values converted to SI base units.
    """)
    return


@app.cell
def _(axial_stress_eq, fa_inputs):
    axial_stress_eq.sym_evalf(
        subs=fa_inputs,
        output_unit="MPa",
        decimals=5,
        mode="verbose",
    )
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    `mode="one_line"` collapses the equation, subtituted quantities and result onto a single line:
    """)
    return


@app.cell
def _(axial_stress_eq, fa_inputs):
    axial_stress_eq.sym_evalf(
        subs=fa_inputs,
        output_unit="MPa",
        decimals=1,
        mode="one_line",
    )
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## `quantity_evalf()` on a `DataFrame`

    Now suppose you have done a structural analysis, which gave you the axial forces acting on the members (building columns and beams), and now you want to calculate what the resulting axial stresses on these members are. So, let's:

    1. create a `polars.DataFrame` with the forces and cross-sectional areas of these members;
    2. calculate the axial stresses using `quantity_evalf()` on the `DataFrame`;
    3. symbolicly evaluate the axial stress in the member which we select from a `marimo.ui.table` widget.
    """)
    return


@app.cell(hide_code=True)
def _(Quantity, Symbol, axial_stress_eq, mo, pl):
    # 1. Forces are in kN, areas in mm^2.
    members = pl.DataFrame(
        {
            "member_type": ["column", "column", "brace", "strut", "tie"],
            "section": ["W14x90", "HSS8x8x5/8", "HSS6x6x3/8", "L4x4", "C8x11.5"],
            "F_kN": [-720.0, -680, 340.0, -110.0, 250.0],
            "A_mm2": [17_100.0, 10_580, 4_890.0, 1_870.0, 2_168.0],
        }
    )

    # 2. Vectorise via polars: build a Quantity per row, evaluate to MPa, take the
    # magnitude. Returning the bare float keeps the column polars-native.
    _axial_stress_expr = axial_stress_eq.rhs

    def _stress_MPa(row):
        return quantity_evalf(
            expr=_axial_stress_expr,
            subs={
                Symbol("F"): Quantity(row["F_kN"], "kN"),
                Symbol("A"): Quantity(row["A_mm2"], "mm^2"),
            },
            output_unit="MPa",
        ).magnitude

    # Apply the vectorized function to the polars dataframe to calculate the axial stresses in the members.
    members_with_stress = members.with_columns(
        pl.struct(["F_kN", "A_mm2"])
        .map_elements(_stress_MPa, return_dtype=pl.Float64)
        .round(2)
        .alias("sigma_MPa")
    )

    # 3a. Create a marimo ui element in which you can select the member for which
    # you want to symbolicly evaluate the calculation.
    selected_member_to_symeval = mo.ui.table(
        members_with_stress, selection="single", initial_selection=[1]
    )
    selected_member_to_symeval
    return (selected_member_to_symeval,)


@app.cell(hide_code=True)
def _(Quantity, Symbol, axial_stress_eq, selected_member_to_symeval):
    # 3b. Do the symbolic evaluation for the selected member
    _sel_row = selected_member_to_symeval.value
    axial_stress_eq.sym_evalf(
        subs={
            Symbol("F"): Quantity(_sel_row["F_kN"][0], "kN"),
            Symbol("A"): Quantity(_sel_row["A_mm2"][0], "mm^2"),
        },
        output_unit="MPa",
        decimals=1,
    )
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Axial Resistance of a Steel HSS Member
    as per CSA S16-17.

    This is the example calculation that Connor Ferster, the author of [`handcalcs`](https://github.com/connorferster/handcalcs) (huge [inspiration](https://github.com/bedrock-engineer/symeval#inspiration) for SymEval), shows in [this "Engineering Calculations: Handcalcs-on-Jupyter vs. Excel" YouTube tutorial](https://www.youtube.com/watch?v=n9Uzy3Eb-XI).

    This example shows how you can define an entire table of inputs using marimo ui elements and then chain the result from one equation into the next.
    """)
    return


@app.cell(hide_code=True)
def _(mo):
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

    # Input table: each row carries its sympy.Symbol, unit, and default value/step.
    # The mo.ui.number elements and the markdown table are both derived from this input table.
    input_table = [
        {"section": "Loads"},
        {
            "name": "Compressive force",
            "symbol": compressive_force,
            "unit": "kN",
            "value": 680,
        },
        {"section": "Member geometry"},
        {
            "name": "Beam length",
            "symbol": beam_length,
            "unit": "m",
            "value": 6.5,
            "step": 0.1,
        },
        {
            "name": "Effective length factor",
            "symbol": effective_length_factor,
            "value": 1,
            "step": 0.1,
        },
        {"section": "Material properties"},
        {
            "name": "Elastic modulus",
            "symbol": elastic_modulus,
            "unit": "GPa",
            "value": 200,
        },
        {
            "name": "Yield strength",
            "symbol": yield_strength,
            "unit": "MPa",
            "value": 400,
        },
        {
            "name": "Strain-hardening exponent",
            "symbol": strain_hardening_exponent,
            "value": 1.34,
            "step": 0.01,
        },
        {
            "name": "Strength reduction factor",
            "symbol": strength_reduction_factor,
            "value": 0.85,
            "step": 0.05,
        },
        {"section": "Member section properties"},
        {
            "name": "Cross-sectional area",
            "symbol": cross_sectional_area,
            "unit": "mm^2",
            "value": 10_580,
        },
        {
            "name": "Radius of gyration about the y-axis",
            "symbol": radius_gyration,
            "unit": "mm",
            "value": 76.1,
            "step": 0.1,
        },
    ]

    input_uis = mo.ui.dictionary(
        {
            s["name"]: mo.ui.number(value=s["value"], step=s.get("step"))
            for s in input_table
            if "name" in s
        }
    )

    def _table_row(s):
        if "section" in s:
            return f"| **{s['section']}** |  |  |  |  |"
        unit = f"${s['unit']}$" if s.get("unit") else ""
        return (
            f"| {s['name']} | ${s['symbol']}$ | = | {input_uis[s['name']]} | {unit} |"
        )

    input_table_md = mo.md(
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
        input_table_md,
        input_uis,
        radius_gyration,
        strain_hardening_exponent,
        strength_reduction_factor,
        yield_strength,
    )


@app.cell(hide_code=True)
def _(input_table_md, mo):
    mo.md(f"""
    {input_table_md}
    """)
    return


@app.cell(hide_code=True)
def _(
    Equality,
    Quantity,
    beam_length,
    compressive_force,
    cross_sectional_area,
    effective_length_factor,
    elastic_modulus,
    input_table,
    input_uis,
    mo,
    radius_gyration,
    strain_hardening_exponent,
    strength_reduction_factor,
    yield_strength,
):
    # Like before, create a dictionary with sympy.Symbol keys and pint.Quantity values:
    symbolic_quantities = {
        s["symbol"]: Quantity(input_uis[s["name"]].value, s.get("unit"))
        for s in input_table
        if "name" in s
    }
    # then define the equation:
    _euler_buckling_eq = Equality(
        sympy.Symbol("F_e"),
        (sympy.pi**2 * elastic_modulus)
        / ((beam_length * effective_length_factor / radius_gyration) ** 2),
    )
    # and symbolically evaluate it:
    euler_buckling_stress = _euler_buckling_eq.sym_evalf(
        subs=symbolic_quantities,
        output_unit="GPa",
        decimals=3,
        mode="one_line",
    )
    # But now, in order to chain the Euler buckling stress into the next equation,
    # add it to the dictionary with symbolic quantities:
    symbolic_quantities[euler_buckling_stress.symbol] = euler_buckling_stress.quantity

    # Rinse and repeat:
    # Lambda factor
    _lambda_factor_eq = Equality(
        sympy.Symbol(r"\lambda"),
        (sympy.sqrt(yield_strength / euler_buckling_stress.symbol))
        ** (2 * strain_hardening_exponent),
    )
    lambda_factor = _lambda_factor_eq.sym_evalf(
        subs=symbolic_quantities,
        decimals=3,
        mode="one_line",
    )
    symbolic_quantities[lambda_factor.symbol] = lambda_factor.quantity

    # Axial resistance
    _axial_resistance_eq = Equality(
        sympy.Symbol("C_r"),
        (strength_reduction_factor * cross_sectional_area * yield_strength)
        / ((1 + lambda_factor.symbol) ** (1 / strain_hardening_exponent)),
    )
    axial_resistance = _axial_resistance_eq.sym_evalf(
        subs=symbolic_quantities,
        output_unit="MN",
        decimals=3,
        mode="one_line",
    )
    symbolic_quantities[axial_resistance.symbol] = axial_resistance.quantity

    # Demand capacity ratio
    _dcr_eq = Equality(
        sympy.Symbol("DCR"),
        compressive_force / axial_resistance.symbol,
    )
    dcr = _dcr_eq.sym_evalf(
        subs=symbolic_quantities,
        decimals=3,
        mode="one_line",
    )
    symbolic_quantities[dcr.symbol] = dcr.quantity

    # Show the whole calulation:
    mo.vstack(
        [
            # mo.md("### Calculation"),
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


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Ideal Gas Law

    When solving the ideal gas law
    """)
    return


@app.cell(hide_code=True)
def _(Equality, Quantity, mo):
    # Define Ideal Gas Law sympy.Symbols, Equation and dictionary of variables with units
    P_sym, V_sym, T_sym, n_sym, R_sym = sympy.symbols("P V T n R")
    ideal_gas_law = Equality(P_sym * V_sym, R_sym * T_sym * n_sym)
    R_q = Quantity(1, "molar_gas_constant").to("J/(mol*K)")

    ideal_gas_law_vars = {
        "P (kPa)": (P_sym, "kPa"),
        "V (Liters)": (V_sym, "l"),
        "T (K)": (T_sym, "K"),
        "n (mol)": (n_sym, "mol"),
    }
    ideal_gas_law_options = list(ideal_gas_law_vars)

    mo.md(rf"""
    $${sympy.latex(ideal_gas_law)}$$

    you need to always know three out of four variables ($R = {R_q:.4f~L}$ is the molar gas constant):

    | Name | Symbol | SI-unit |
    |------|--------|---------|
    | Pressure | $P$ | $Pa$ |
    | Volume | $V$ | $m^3$ |
    | Temperature | $T$ | $K$ |
    | Number of gas particles | $n$ | $mol$ |
    """)
    return (
        P_sym,
        R_q,
        R_sym,
        T_sym,
        V_sym,
        ideal_gas_law,
        ideal_gas_law_options,
        ideal_gas_law_vars,
        n_sym,
    )


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    Now, given that SymEval is built on top of SymPy, SymEval will first symbolically rearrange the ideal gas law to isolate our unknown variable on the lefthand side with `sympy.solve`. After which the resulting expression feeds straight into `sym_evalf`.

    The marimo ui elements combined with the piston widget are meant to give an [explorable explanation](https://worrydream.com/ExplorableExplanations/) of and some intuition for the ideal gas law.
    """)
    return


@app.cell(hide_code=True)
def _(ideal_gas_law_options, mo):
    solve_for_radio = mo.ui.radio(
        options=ideal_gas_law_options,
        value="P (kPa)",
    )
    return (solve_for_radio,)


@app.cell(hide_code=True)
def _(mo, solve_for_radio):
    P_input = mo.ui.slider(
        start=1,
        stop=500,
        step=1,
        value=101.325,
        debounce=True,
        include_input=True,
        disabled=solve_for_radio.value == "P (kPa)",
    )
    V_input = mo.ui.slider(
        start=5,
        stop=100,
        step=0.5,
        value=22.4,
        debounce=True,
        include_input=True,
        disabled=solve_for_radio.value == "V (Liters)",
    )
    T_input = mo.ui.slider(
        start=100,
        stop=1000,
        step=1,
        value=273.15,
        debounce=True,
        include_input=True,
        disabled=solve_for_radio.value == "T (K)",
    )
    n_input = mo.ui.slider(
        start=0.1,
        stop=10,
        step=0.1,
        value=1.0,
        debounce=True,
        include_input=True,
        disabled=solve_for_radio.value == "n (mol)",
    )

    igl_inputs = {
        "P (kPa)": P_input,
        "V (Liters)": V_input,
        "T (K)": T_input,
        "n (mol)": n_input,
    }

    mo.hstack(
        [solve_for_radio, mo.vstack([P_input, V_input, T_input, n_input])],
        align="center",
        justify="center",
        gap=2,
    )
    return P_input, T_input, V_input, igl_inputs, n_input


@app.cell(hide_code=True)
def _(
    P_input,
    P_sym,
    Quantity,
    R_q,
    R_sym,
    T_input,
    T_sym,
    V_input,
    V_sym,
    ideal_gas_law,
    ideal_gas_law_vars,
    igl_inputs,
    mo,
    n_input,
    n_sym,
    piston_js,
    solve_for_radio,
):
    # Which variable are we solving for? Everything else is a known input.
    _solve_for_label = solve_for_radio.value
    _solve_for_sym, _solve_for_unit = ideal_gas_law_vars[_solve_for_label]

    # Knowns: every slider value except the one we're solving for, plus R.
    _knowns = {
        _sym: Quantity(igl_inputs[_label].value, _unit)
        for _label, (_sym, _unit) in ideal_gas_law_vars.items()
        if _sym != _solve_for_sym
    }
    _knowns[R_sym] = R_q

    # The equation infers its unknown (the one symbol with no value in subs),
    # solves for it, and evaluates: no manual sympy.solve, no output_symbol.
    igl_sym_eval = ideal_gas_law.sym_evalf(
        subs=_knowns,
        output_unit=_solve_for_unit,
        decimals=2,
    )

    # Knowns plus the solved unknown: the full set the piston widget renders.
    _symbolic_quantities = {**_knowns, _solve_for_sym: igl_sym_eval.quantity}

    # Put the knowns, unknowns and their slider bounds into JavaScript constants
    _js_consts = f"""
    const P = {_symbolic_quantities[P_sym].magnitude};
    const V = {_symbolic_quantities[V_sym].magnitude};
    const T = {_symbolic_quantities[T_sym].magnitude};
    const n = {_symbolic_quantities[n_sym].magnitude};

    const V_MIN = {V_input.start}, V_MAX = {V_input.stop};
    const P_MIN = {P_input.start}, P_MAX = {P_input.stop};
    const T_MIN = {T_input.start}, T_MAX = {T_input.stop};
    const N_MIN = {n_input.start}, N_MAX = {n_input.stop};
    """

    # Out Of Bounds detection: when the widget cannot display the value that
    # was solved for, this happens for example when the weight can't become bigger,
    # but P can. Note: only the solve-for variable can land out of range.
    _solve_for_input = igl_inputs[_solve_for_label]
    _solve_for_value = float(igl_sym_eval.magnitude)
    # Out Of Bounds message & HTML
    # T is exempt: the particle speed follows the raw T at any value, so the visual
    # stays honest outside the slider range. Only the tint saturates.
    _oob_msg = ""
    if str(_solve_for_sym) != "T":
        if _solve_for_value < _solve_for_input.start:
            _oob_msg = (
                f"\U0001f4a5 Solved <b>{_solve_for_label}</b> = {_solve_for_value:.3g}, "
                f"below min ({_solve_for_input.start}). Visual is floored; see symbolic evaluation."
            )
        elif _solve_for_value > _solve_for_input.stop:
            _oob_msg = (
                f"\U0001f4a5 Solved <b>{_solve_for_label}</b> = {_solve_for_value:.3g}, "
                f"above max ({_solve_for_input.stop}). Visual is capped; see symbolic evaluation."
            )
    _oob_html = (
        f'<div style="position:absolute;top:4px;left:4px;right:4px;'
        f"font-family:sans-serif;font-size:10.5px;line-height:1.25;"
        f"background:rgba(255,238,238,0.75);border:1px solid #d33;"
        f'border-radius:4px;padding:3px 6px;color:#900;">{_oob_msg}</div>'
        if _oob_msg
        else ""
    )

    # mo.iframe flattens newlines in its HTML serialization, so // line comments
    # would swallow the rest of the (now one-line) script. Convert them to /* */
    # so they survive. See research/issues/marimo--iframe-strips-newlines.md.
    import re as _re

    _piston_js = _re.sub(r"//([^\n]*)", r"/*\1 */", piston_js)

    _piston_html = f"""<!doctype html>
    <html>
    <body style="margin:0;padding:0;background:#ffffff">
    <div style="position:relative;width:270px;height:360px;">
      <canvas id="piston-canvas" width="270" height="360" style="display:block;"></canvas>
      {_oob_html}
    </div>
    <script>
    {_js_consts}
    {_piston_js}
    </script>
    </body></html>"""

    _piston_iframe = mo.iframe(_piston_html, width="290px", height="380px")

    mo.hstack(
        [_piston_iframe, mo.vstack([ideal_gas_law, igl_sym_eval])],
        align="center",
        gap=2,
    )
    return


@app.cell(hide_code=True)
def _():
    piston_js = r"""
    // piston_js
    // Canvas and cylinder dimensions
    const c = document.getElementById("piston-canvas");
    const ctx2d = c.getContext("2d");
    const W = c.width;
    const H = c.height;
    const CYL_X = 70;
    const CYL_W = 130;
    const TOP_MARGIN = 110;
    const BOTTOM_MARGIN = 20;
    const CYL_BOTTOM = H - BOTTOM_MARGIN;

    // Calculate normalized (0 - 1) volume, pressure, temperature & No. particles
    const v01 = Math.max(0, Math.min(1, (V - V_MIN) / (V_MAX - V_MIN)));
    const p01 = Math.max(0, Math.min(1, (P - P_MIN) / (P_MAX - P_MIN)));
    const t01 = Math.max(0, Math.min(1, (T - T_MIN) / (T_MAX - T_MIN)));
    const n01 = Math.max(0, Math.min(1, (n - N_MIN) / (N_MAX - N_MIN)));

    // V -> gas column height
    // V at V_MIN gives GAS_MIN, V at V_MAX gives GAS_MAX
    // gasHeight & pistonY scale linearly across the V-slider range
    const GAS_MIN = 10;
    const GAS_MAX = H - TOP_MARGIN - BOTTOM_MARGIN;
    const gasHeight = GAS_MIN + v01 * (GAS_MAX - GAS_MIN);
    const pistonY = CYL_BOTTOM - gasHeight;

    // P -> trapezoidal weight block size
    // Until the middle of the P-range, the weight grows in all directions
    // as P increases. At higher P's the weight only scales vertically.
    const WEIGHT_W_MIN = 40;
    const WEIGHT_W_MAX = CYL_W - 6;
    const WEIGHT_H_MIN = 18;
    const WEIGHT_H_MID = 45;
    const WEIGHT_H_MAX = 90;
    const PHASE_SPLIT = 0.5;
    let weightWBottom, weightH;
    if (p01 <= PHASE_SPLIT) {
      const k = p01 / PHASE_SPLIT;
      weightWBottom = WEIGHT_W_MIN + k * (WEIGHT_W_MAX - WEIGHT_W_MIN);
      weightH = WEIGHT_H_MIN + k * (WEIGHT_H_MID - WEIGHT_H_MIN);
    } else {
      const k = (p01 - PHASE_SPLIT) / (1 - PHASE_SPLIT);
      weightWBottom = WEIGHT_W_MAX;
      weightH = WEIGHT_H_MID + k * (WEIGHT_H_MAX - WEIGHT_H_MID);
    }
    const weightWTop = weightWBottom * 0.55;

    // T -> particle speed + warm/cool tint
    const speed = Math.sqrt(T) * 0.11;
    const tintR = Math.round(80 + t01 * (240 - 80));
    const tintG = Math.round(140 - t01 * 80);
    const tintB = Math.round(240 - t01 * 200);
    const tint = `rgb(${tintR},${tintG},${tintB})`;

    // n -> particle count
    const N_PARTICLES_MIN = 4;
    const N_PARTICLES_MAX = 250;
    const nParticles = Math.max(
      N_PARTICLES_MIN,
      Math.min(N_PARTICLES_MAX, Math.round(n01 * N_PARTICLES_MAX)),
    );

    const particles = [];
    for (let i = 0; i < nParticles; i++) {
      const ang = Math.random() * Math.PI * 2;
      particles.push({
        x: CYL_X + 4 + Math.random() * (CYL_W - 8),
        y: pistonY + 4 + Math.random() * (gasHeight - 8),
        vx: Math.cos(ang),
        vy: Math.sin(ang),
      });
    }

    function draw() {
      ctx2d.clearRect(0, 0, W, H);

      ctx2d.strokeStyle = "#888";
      ctx2d.lineWidth = 2;
      ctx2d.beginPath();
      ctx2d.moveTo(CYL_X, TOP_MARGIN);
      ctx2d.lineTo(CYL_X, CYL_BOTTOM);
      ctx2d.lineTo(CYL_X + CYL_W, CYL_BOTTOM);
      ctx2d.lineTo(CYL_X + CYL_W, TOP_MARGIN);
      ctx2d.stroke();

      const cx = CYL_X + CYL_W / 2;
      const wBL = cx - weightWBottom / 2;
      const wBR = cx + weightWBottom / 2;
      const wTL = cx - weightWTop / 2;
      const wTR = cx + weightWTop / 2;
      const wBY = pistonY - 4;
      const wTY = wBY - weightH;
      ctx2d.fillStyle = "#5a5a5a";
      ctx2d.strokeStyle = "#333";
      ctx2d.lineWidth = 1.5;
      ctx2d.beginPath();
      ctx2d.moveTo(wBL, wBY);
      ctx2d.lineTo(wBR, wBY);
      ctx2d.lineTo(wTR, wTY);
      ctx2d.lineTo(wTL, wTY);
      ctx2d.closePath();
      ctx2d.fill();
      ctx2d.stroke();

      // Ring handle: outer radius AND thickness both scale with P. Inner hole
      // is always smaller than the ring thickness, so the ring reads as a
      // chunky rim at all sizes.
      const ringOuterR = 5 + p01 * 6; // 5 -> 11 px
      const ringThickness = 2.5 + p01 * 3; // 2.5 -> 5.5 px
      const ringInnerR = Math.max(1, ringOuterR - ringThickness);
      const ringCenterY = wTY - ringOuterR + 2;
      ctx2d.fillStyle = "#333";
      ctx2d.beginPath();
      ctx2d.arc(cx, ringCenterY, ringOuterR, 0, Math.PI * 2);
      ctx2d.arc(cx, ringCenterY, ringInnerR, 0, Math.PI * 2, true);
      ctx2d.closePath();
      ctx2d.fill();

      ctx2d.fillStyle = "#fff";
      const fontSize = Math.min(18, weightH * 0.55);
      ctx2d.font = fontSize + "px sans-serif";
      ctx2d.textAlign = "center";
      ctx2d.textBaseline = "middle";
      ctx2d.fillText("kg", cx, (wBY + wTY) / 2);

      ctx2d.fillStyle = "#aaa";
      ctx2d.strokeStyle = "#333";
      ctx2d.lineWidth = 1;
      ctx2d.fillRect(CYL_X, pistonY - 4, CYL_W, 8);
      ctx2d.strokeRect(CYL_X, pistonY - 4, CYL_W, 8);

      ctx2d.fillStyle = tint;
      for (const p of particles) {
        const mag = Math.hypot(p.vx, p.vy) || 1;
        const sx = (p.vx / mag) * speed;
        const sy = (p.vy / mag) * speed;
        p.x += sx;
        p.y += sy;
        if (p.x < CYL_X + 3) {
          p.x = CYL_X + 3;
          p.vx = Math.abs(p.vx);
        } else if (p.x > CYL_X + CYL_W - 3) {
          p.x = CYL_X + CYL_W - 3;
          p.vx = -Math.abs(p.vx);
        }
        if (p.y < pistonY + 5) {
          p.y = pistonY + 5;
          p.vy = Math.abs(p.vy);
        } else if (p.y > CYL_BOTTOM - 3) {
          p.y = CYL_BOTTOM - 3;
          p.vy = -Math.abs(p.vy);
        }
        ctx2d.beginPath();
        ctx2d.arc(p.x, p.y, 2.4, 0, Math.PI * 2);
        ctx2d.fill();
      }

      requestAnimationFrame(draw);
    }
    requestAnimationFrame(draw);
    // piston_js
    """
    return (piston_js,)


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    1. Edit the JavaScript code of the piston here with syntax highlighting.
    2. Copy the JS code into the string in the `piston_js` variable in the Python cell above.

    ```js
    // piston_js
    // Canvas and cylinder dimensions
    const c = document.getElementById("piston-canvas");
    const ctx2d = c.getContext("2d");
    const W = c.width;
    const H = c.height;
    const CYL_X = 70;
    const CYL_W = 130;
    const TOP_MARGIN = 110;
    const BOTTOM_MARGIN = 20;
    const CYL_BOTTOM = H - BOTTOM_MARGIN;

    // Calculate normalized (0 - 1) volume, pressure, temperature & No. particles
    const v01 = Math.max(0, Math.min(1, (V - V_MIN) / (V_MAX - V_MIN)));
    const p01 = Math.max(0, Math.min(1, (P - P_MIN) / (P_MAX - P_MIN)));
    const t01 = Math.max(0, Math.min(1, (T - T_MIN) / (T_MAX - T_MIN)));
    const n01 = Math.max(0, Math.min(1, (n - N_MIN) / (N_MAX - N_MIN)));

    // V -> gas column height
    // V at V_MIN gives GAS_MIN, V at V_MAX gives GAS_MAX
    // gasHeight & pistonY scale linearly across the V-slider range
    const GAS_MIN = 10;
    const GAS_MAX = H - TOP_MARGIN - BOTTOM_MARGIN;
    const gasHeight = GAS_MIN + v01 * (GAS_MAX - GAS_MIN);
    const pistonY = CYL_BOTTOM - gasHeight;

    // P -> trapezoidal weight block size
    // Until the middle of the P-range, the weight grows in all directions
    // as P increases. At higher P's the weight only scales vertically.
    const WEIGHT_W_MIN = 40;
    const WEIGHT_W_MAX = CYL_W - 6;
    const WEIGHT_H_MIN = 18;
    const WEIGHT_H_MID = 45;
    const WEIGHT_H_MAX = 90;
    const PHASE_SPLIT = 0.5;
    let weightWBottom, weightH;
    if (p01 <= PHASE_SPLIT) {
      const k = p01 / PHASE_SPLIT;
      weightWBottom = WEIGHT_W_MIN + k * (WEIGHT_W_MAX - WEIGHT_W_MIN);
      weightH = WEIGHT_H_MIN + k * (WEIGHT_H_MID - WEIGHT_H_MIN);
    } else {
      const k = (p01 - PHASE_SPLIT) / (1 - PHASE_SPLIT);
      weightWBottom = WEIGHT_W_MAX;
      weightH = WEIGHT_H_MID + k * (WEIGHT_H_MAX - WEIGHT_H_MID);
    }
    const weightWTop = weightWBottom * 0.55;

    // T -> particle speed + warm/cool tint
    const speed = Math.sqrt(T) * 0.11;
    const tintR = Math.round(80 + t01 * (240 - 80));
    const tintG = Math.round(140 - t01 * 80);
    const tintB = Math.round(240 - t01 * 200);
    const tint = `rgb(${tintR},${tintG},${tintB})`;

    // n -> particle count
    const N_PARTICLES_MIN = 4;
    const N_PARTICLES_MAX = 250;
    const nParticles = Math.max(
      N_PARTICLES_MIN,
      Math.min(N_PARTICLES_MAX, Math.round(n01 * N_PARTICLES_MAX)),
    );

    const particles = [];
    for (let i = 0; i < nParticles; i++) {
      const ang = Math.random() * Math.PI * 2;
      particles.push({
        x: CYL_X + 4 + Math.random() * (CYL_W - 8),
        y: pistonY + 4 + Math.random() * (gasHeight - 8),
        vx: Math.cos(ang),
        vy: Math.sin(ang),
      });
    }

    function draw() {
      ctx2d.clearRect(0, 0, W, H);

      ctx2d.strokeStyle = "#888";
      ctx2d.lineWidth = 2;
      ctx2d.beginPath();
      ctx2d.moveTo(CYL_X, TOP_MARGIN);
      ctx2d.lineTo(CYL_X, CYL_BOTTOM);
      ctx2d.lineTo(CYL_X + CYL_W, CYL_BOTTOM);
      ctx2d.lineTo(CYL_X + CYL_W, TOP_MARGIN);
      ctx2d.stroke();

      const cx = CYL_X + CYL_W / 2;
      const wBL = cx - weightWBottom / 2;
      const wBR = cx + weightWBottom / 2;
      const wTL = cx - weightWTop / 2;
      const wTR = cx + weightWTop / 2;
      const wBY = pistonY - 4;
      const wTY = wBY - weightH;
      ctx2d.fillStyle = "#5a5a5a";
      ctx2d.strokeStyle = "#333";
      ctx2d.lineWidth = 1.5;
      ctx2d.beginPath();
      ctx2d.moveTo(wBL, wBY);
      ctx2d.lineTo(wBR, wBY);
      ctx2d.lineTo(wTR, wTY);
      ctx2d.lineTo(wTL, wTY);
      ctx2d.closePath();
      ctx2d.fill();
      ctx2d.stroke();

      // Ring handle: outer radius AND thickness both scale with P. Inner hole
      // is always smaller than the ring thickness, so the ring reads as a
      // chunky rim at all sizes.
      const ringOuterR = 5 + p01 * 6; // 5 -> 11 px
      const ringThickness = 2.5 + p01 * 3; // 2.5 -> 5.5 px
      const ringInnerR = Math.max(1, ringOuterR - ringThickness);
      const ringCenterY = wTY - ringOuterR + 2;
      ctx2d.fillStyle = "#333";
      ctx2d.beginPath();
      ctx2d.arc(cx, ringCenterY, ringOuterR, 0, Math.PI * 2);
      ctx2d.arc(cx, ringCenterY, ringInnerR, 0, Math.PI * 2, true);
      ctx2d.closePath();
      ctx2d.fill();

      ctx2d.fillStyle = "#fff";
      const fontSize = Math.min(18, weightH * 0.55);
      ctx2d.font = fontSize + "px sans-serif";
      ctx2d.textAlign = "center";
      ctx2d.textBaseline = "middle";
      ctx2d.fillText("kg", cx, (wBY + wTY) / 2);

      ctx2d.fillStyle = "#aaa";
      ctx2d.strokeStyle = "#333";
      ctx2d.lineWidth = 1;
      ctx2d.fillRect(CYL_X, pistonY - 4, CYL_W, 8);
      ctx2d.strokeRect(CYL_X, pistonY - 4, CYL_W, 8);

      ctx2d.fillStyle = tint;
      for (const p of particles) {
        const mag = Math.hypot(p.vx, p.vy) || 1;
        const sx = (p.vx / mag) * speed;
        const sy = (p.vy / mag) * speed;
        p.x += sx;
        p.y += sy;
        if (p.x < CYL_X + 3) {
          p.x = CYL_X + 3;
          p.vx = Math.abs(p.vx);
        } else if (p.x > CYL_X + CYL_W - 3) {
          p.x = CYL_X + CYL_W - 3;
          p.vx = -Math.abs(p.vx);
        }
        if (p.y < pistonY + 5) {
          p.y = pistonY + 5;
          p.vy = Math.abs(p.vy);
        } else if (p.y > CYL_BOTTOM - 3) {
          p.y = CYL_BOTTOM - 3;
          p.vy = -Math.abs(p.vy);
        }
        ctx2d.beginPath();
        ctx2d.arc(p.x, p.y, 2.4, 0, Math.PI * 2);
        ctx2d.fill();
      }

      requestAnimationFrame(draw);
    }
    requestAnimationFrame(draw);
    // piston_js
    ```
    """)
    return


@app.cell(column=1, hide_code=True)
def _(mo):
    mo.md(r"""
    # `pytest` Tests
    """)
    return


@app.cell
def _(Quantity):
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
        """**evalf_kwargs are passed through to expr.evalf; passing `n` shouldn\'t crash."""
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
def _(Quantity):
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

    def test_sym_evalf_wraps_unit_under_exponent():
        """A unit-carrying value under a power is wrapped in \\left(...\\right) so the exponent binds the whole quantity."""
        x = sympy.Symbol("x")
        out = sym_evalf(x**2, subs={x: Quantity(3, "m")}, output_symbol="y").latex
        assert r"\left(" in out and r"\right)" in out

    def test_sym_evalf_preserves_equal_valued_terms():
        """Distinct symbols with equal values stay a sum in the substituted form (3 m + 3 m, not folded to 6 m)."""
        x, y = sympy.symbols("x y")
        out = sym_evalf(
            x + y,
            subs={x: Quantity(3, "m"), y: Quantity(3, "m")},
            output_symbol="z",
        ).latex
        # multi_line carries a '+' in both the symbolic and the substituted line;
        # folding 3 m + 3 m to 6 m would drop the substituted line's '+'.
        assert out.count("+") >= 2

    def test_symbolic_evaluation_delegates_to_quantity():
        """SymbolicEvaluation delegates the whole Quantity surface via __getattr__."""
        F, A = sympy.symbols("F A")
        result = sym_evalf(
            F / A,
            subs={F: Quantity(50, "kN"), A: Quantity(100, "mm^2")},
            output_symbol="sigma",
            output_unit="MPa",
            decimals=2,
        )
        # to_reduced_units was never a hand-written forward -> exercises __getattr__
        assert (
            result.to_reduced_units().magnitude
            == result.quantity.to_reduced_units().magnitude
        )
        assert result.m_as("MPa") == result.quantity.m_as("MPa")
        assert result.units == result.quantity.units
        # the added surface still works
        assert result.symbol == sympy.Symbol("sigma")
        assert isinstance(result.latex, str) and result.latex


    return


@app.cell
def _(Quantity):
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
def _(Quantity, stress_calc):
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


@app.cell
def _(Quantity):
    def ideal_gas_R():
        return Quantity(1, "molar_gas_constant").to("J/(mol*K)")

    return (ideal_gas_R,)


@app.cell
def _(Equality, Quantity, ideal_gas_R):
    def test_sym_evalf_equation_infers_output_symbol():
        """Eq with a bare-symbol LHS infers the output symbol from that LHS."""
        F, A, sigma = sympy.symbols("F A sigma")
        result = Equality(sigma, F / A).sym_evalf(
            subs={F: Quantity(-680, "kN"), A: Quantity(10_580, "mm^2")},
            output_unit="MPa",
            decimals=2,
        )
        assert result.symbol == sigma
        assert abs(result.quantity.magnitude - (-64.27)) < 0.01
        assert r"\sigma" in result._repr_latex_()

    def test_sym_evalf_equation_solves_embedded_unknown():
        """Eq whose unknown is embedded (P*V = nRT) is solved before evaluating."""
        P, V, n, R, T = sympy.symbols("P V n R T")
        igl = Equality(P * V, R * T * n)
        knowns = {
            V: Quantity(22.4, "l"),
            R: ideal_gas_R(),
            T: Quantity(273.15, "K"),
            n: Quantity(1, "mol"),
        }
        result = igl.sym_evalf(subs=knowns, output_unit="kPa", decimals=2)
        assert result.symbol == P
        assert abs(result.quantity.magnitude - 101.39) < 0.01

    def test_sym_evalf_equation_solve_for_is_data_driven():
        """The same equation solves for whichever symbol is left out of subs."""
        P, V, n, R, T = sympy.symbols("P V n R T")
        igl = Equality(P * V, R * T * n)
        result = igl.sym_evalf(
            subs={
                P: Quantity(101.325, "kPa"),
                V: Quantity(22.4, "l"),
                R: ideal_gas_R(),
                T: Quantity(273.15, "K"),
            },
            output_unit="mol",
            decimals=3,
        )
        assert result.symbol == n
        assert abs(result.quantity.magnitude - 1.0) < 0.01

    def test_sym_evalf_equation_unknown_on_rhs():
        """The unknown may sit on the RHS; the LHS is then the expression."""
        F, A, sigma = sympy.symbols("F A sigma")
        result = Equality(F / A, sigma).sym_evalf(
            subs={F: Quantity(50, "kN"), A: Quantity(100, "mm^2")},
            output_unit="MPa",
            decimals=1,
        )
        assert result.symbol == sigma
        assert abs(result.quantity.magnitude - 500.0) < 0.1

    def test_sym_evalf_equation_matches_expression_latex():
        """Eq(sym, expr) renders identically to expr.sym_evalf(output_symbol=sym)."""
        E, k, L, r_y = sympy.symbols("E k L r_y")
        F_e = sympy.Symbol("F_e")
        expr = (sympy.pi**2 * E) / ((k * L / r_y) ** 2)
        subs = {
            E: Quantity(200, "GPa"),
            k: Quantity(1, ""),
            L: Quantity(6.5, "m"),
            r_y: Quantity(76.1, "mm"),
        }
        from_eq = (
            Equality(F_e, expr)
            .sym_evalf(subs=subs, output_unit="GPa", decimals=3)
            .latex
        )
        from_expr = expr.sym_evalf(
            subs=subs, output_symbol=F_e, output_unit="GPa", decimals=3
        ).latex
        assert from_eq == from_expr

    def test_sym_evalf_equation_explicit_output_symbol_overrides_label():
        """An explicit output_symbol overrides the inferred label on an equation."""
        F, A, sigma = sympy.symbols("F A sigma")
        result = Equality(sigma, F / A).sym_evalf(
            subs={F: Quantity(50, "kN"), A: Quantity(100, "mm^2")},
            output_symbol=r"\tau",
            output_unit="MPa",
            decimals=1,
        )
        assert abs(result.quantity.magnitude - 500.0) < 0.1
        assert r"\tau" in result._repr_latex_()

    def test_sym_evalf_bare_expr_requires_output_symbol():
        """A bare expression still needs output_symbol; omitting it raises."""
        F, A = sympy.symbols("F A")
        try:
            (F / A).sym_evalf(
                subs={F: Quantity(50, "kN"), A: Quantity(100, "mm^2")},
                output_unit="MPa",
            )
        except ValueError as e:
            assert "output_symbol" in str(e)
        else:
            raise AssertionError("Expected ValueError for missing output_symbol")

    def test_sym_evalf_equation_multiple_unknowns_raises():
        """More than one unresolved symbol is ambiguous and raises."""
        P, V, n, R, T = sympy.symbols("P V n R T")
        try:
            Equality(P * V, R * T * n).sym_evalf(
                subs={V: Quantity(22.4, "l"), R: ideal_gas_R()},
                output_unit="kPa",
            )
        except ValueError as e:
            assert "exactly one unknown" in str(e)
        else:
            raise AssertionError("Expected ValueError for multiple unknowns")

    def test_sym_evalf_equation_no_unknown_raises():
        """If every symbol has a value there is nothing to solve for; raises."""
        F, A, sigma = sympy.symbols("F A sigma")
        try:
            Equality(sigma, F / A).sym_evalf(
                subs={
                    sigma: Quantity(1, "Pa"),
                    F: Quantity(1, "N"),
                    A: Quantity(1, "m^2"),
                },
                output_unit="Pa",
            )
        except ValueError as e:
            assert "exactly one unknown" in str(e)
        else:
            raise AssertionError("Expected ValueError for no unknown")

    def test_sym_evalf_equation_non_unique_solution_raises():
        """An equation with several solutions (sigma**2 = F) raises."""
        F, sigma = sympy.symbols("F sigma")
        try:
            Equality(sigma**2, F).sym_evalf(
                subs={F: Quantity(4, "Pa**2")}, output_unit="Pa"
            )
        except ValueError as e:
            assert "solutions" in str(e)
        else:
            raise AssertionError("Expected ValueError for non-unique solution")

    def test_quantity_evalf_rejects_equation():
        """quantity_evalf is expression-only; handing it an Eq raises TypeError."""
        P, V, n, R, T = sympy.symbols("P V n R T")
        try:
            quantity_evalf(
                Equality(P * V, R * T * n),
                subs={V: Quantity(22.4, "l")},
            )
        except TypeError as e:
            assert "sym_evalf" in str(e)
        else:
            raise AssertionError("Expected TypeError for Eq passed to quantity_evalf")

    def test_evalf_method_bindings():
        """sym_evalf is bound on Expr and Equality; quantity_evalf on Expr only."""
        assert hasattr(sympy.Expr, "sym_evalf")
        assert hasattr(sympy.Expr, "quantity_evalf")
        assert hasattr(sympy.Equality, "sym_evalf")
        assert not hasattr(sympy.Equality, "quantity_evalf")

    return


if __name__ == "__main__":
    app.run()
