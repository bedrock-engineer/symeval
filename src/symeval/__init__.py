__all__ = ['quantity_evalf', 'SymbolicEvaluation', 'sym_evalf']


import textwrap
from dataclasses import dataclass, field
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

    A `sympy.Eq` is solved for its single unknown — the one free symbol that
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
            "Expected exactly one unknown — a free symbol of the equation with "
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
            f"({solutions}); symeval needs a unique one. Solve the equation "
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
    `expr.evalf(...)` — so `n`, `maxn`, `chop`, `strict`, `quiet`, and
    `verbose` all work without being listed here individually.

    Args:
        expr (sympy.Expr): The sympy expression to evaluate. Equations are
            not accepted here — use `sym_evalf` for a `sympy.Eq`, or solve
            it first and pass the resulting expression.
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
    if isinstance(expr, sympy.Equality):
        raise TypeError(
            "quantity_evalf evaluates a bare expression, not an equation. "
            "Use sym_evalf for a sympy.Eq (it infers the output symbol), or "
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

    # Placeholder indices follow the canonical sort order of the input symbols,
    # so sympy.Mul ordering matches between the symbolic and substituted forms.
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
        # Wrap a unit-carrying value in \left(...\right) when it sits under an
        # exponent, so the power binds to the whole quantity, not just the unit.
        if not quantity.dimensionless:
            wrapped = rf"\medspace\left({formatted}\right)"
            rendered = rendered.replace(f"{ph_latex}^", f"{wrapped}^")
        rendered = rendered.replace(ph_latex, rf"\medspace{formatted}")
    return rendered

_VALID_MODES = ("multi_line", "verbose", "one_line")

class SymbolicEvaluation:
    """A pint Quantity with an attached LaTeX rendering for marimo/Jupyter.

    Returned by `sym_evalf`. Delegates the common Quantity surface
    (magnitude, units, dimensionality, m, m_as, to, to_base_units) to
    `self.quantity`. `_repr_latex_` returns the rendered LaTeX. `.symbol`
    is the output sympy.Symbol: reference it when building a later equation and
    pair it with `.quantity` in that evaluation's `subs` to chain calculations.
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
    expr: "sympy.Expr | sympy.Equality",
    *,
    subs: dict[sympy.Symbol, pint.Quantity] | None = None,
    output_symbol: str | sympy.Symbol | None = None,
    output_unit: str | pint.Unit | None = None,
    decimals: int = 3,
    mode: Literal["multi_line", "verbose", "one_line"] = "multi_line",
    **evalf_kwargs,
) -> "SymbolicEvaluation":
    """Numerically evaluate `expr` and produce a LaTeX rendering of the working.

    Same numeric kernel as `quantity_evalf`; the addition is the LaTeX
    working attached to the returned `SymbolicEvaluation`.

    Args:
        expr (sympy.Expr | sympy.Equality): The expression to evaluate,
            or a `sympy.Eq` whose single unknown (the free symbol absent from
            `subs`) is solved for. For an equation the output symbol is
            inferred, so `output_symbol` may be omitted.
        subs (dict[sympy.Symbol, pint.Quantity] | None): Mapping from
            `sympy.Symbol` to `pint.Quantity` (or a scalar for dimensionless
            inputs). Same shape as sympy.evalf's `subs` kwarg. Defaults to
            None (no substitutions).
        output_symbol (str | sympy.Symbol | None): LaTeX label for the
            output — a string like `r"\\sigma"` or a `sympy.Symbol`. The label
            appears on the left of every line of the rendered working.
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
            LaTeX working attached. Renders in marimo / Jupyter via
            `_repr_latex_`. Has `.quantity`, `.latex`, and `.symbol` for
            chaining into downstream sympy expressions.

    Raises:
        ValueError: If `mode` is not one of the allowed values.
    """
    if mode not in _VALID_MODES:
        raise ValueError(f"mode must be one of {_VALID_MODES}, got {mode!r}")
    subs = subs or {}
    expr, _inferred_symbol = _resolve_formula(expr, subs)
    if output_symbol is None:
        if _inferred_symbol is None:
            raise ValueError(
                "output_symbol is required when evaluating a bare sympy "
                "expression. Pass a sympy.Eq instead and the output symbol "
                "is inferred from the equation."
            )
        output_symbol = _inferred_symbol

    # Step 1: Symbolic LaTeX (formula with symbols).
    expression_latex = sympy.latex(expr)

    # Step 2: the substituted form (formula with numbers spliced in).
    substituted_latex = _render_substituted(expr, subs, decimals)

    # Step 2.5 (verbose only): the substituted form in SI base units.
    si_substituted_latex = None
    if mode == "verbose":
        si_substituted_latex = _render_substituted(
            expr, subs, decimals, si_stripped=True
        )

    # Step 3: Numerical evaluation. Delegate to quantity_evalf, which forwards
    # the evalf kwargs.
    output_quantity = quantity_evalf(
        expr, subs=subs, output_unit=output_unit, **evalf_kwargs
    )

    # Result line: the value in its own unit, plus a prefix-stripped
    # scientific dual when the unit carries an SI prefix (see _format_result).
    output_var_unit_latex, output_dual_latex = _format_result(
        output_quantity, decimals
    )

    # Coerce output_symbol to a sympy.Symbol for both rendering and chaining.
    if isinstance(output_symbol, sympy.Symbol):
        output_sym = output_symbol
    else:
        output_sym = sympy.Symbol(str(output_symbol))
    sym_latex = sympy.latex(output_sym)
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

# Method bindings so users can write `expr.sym_evalf(...)`,
# `equation.sym_evalf(...)`, or `expr.quantity_evalf(...)`.
#
# sym_evalf accepts an equation (it infers the output symbol from the
# equation), so it's bound on Equality as well as Expr — mirroring how
# sympy's own `.subs`/`.evalf` live on Basic and work on both. quantity_evalf
# is the bare-value fast path (no label to infer) and stays expression-only,
# so it's bound on Expr alone. Bind the functions directly (not via lambdas)
# so introspection tools — `help`, marimo's 'View live docs', IDE hovers —
# see the real signature and docstring rather than a generic `lambda(**kw)`.
sympy.Expr.quantity_evalf = quantity_evalf
sympy.Expr.sym_evalf = sym_evalf
sympy.Equality.sym_evalf = sym_evalf
