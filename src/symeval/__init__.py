__all__ = ['quantity_evalf', 'SymbolicEvaluation', 'sym_evalf']


import warnings
from dataclasses import dataclass
from decimal import Decimal
from typing import Literal

import pint
import sympy


def _quantity_to_sympy_base(quantity: pint.Quantity) -> sympy.Expr:
    """Convert a pint quantity to a sympy expression in base SI units.

    Dimensionless quantities return their bare magnitude (a Python float).

    Units use their full names ("kilogram", "meter"), not abbreviations: an
    abbreviated unit becomes a sympy symbol like `m` that is indistinguishable
    from an input symbol named `m` (mass, say), silently corrupting the
    substitution. Full names keep the unit symbols out of the namespace of
    typical input symbols; `quantity_evalf` guards the residual collisions.
    """
    if quantity.dimensionality == {}:
        return quantity.magnitude
    base = quantity.to_base_units()
    sympy_units = sympy.sympify(f"{base.units:D}")
    return base.magnitude * sympy_units

def _coerce_subs(
    subs: "dict[sympy.Symbol, pint.Quantity | float] | None",
) -> "tuple[dict[sympy.Symbol, pint.Quantity], pint.UnitRegistry]":
    """Normalise `subs`: plain numbers become dimensionless quantities.

    Mirrors sympy's `evalf`, which accepts bare numbers in its `subs`. The
    registry is read from the first pint quantity in `subs` (falling back to
    Pint's application registry), so coerced values land in the same registry
    as the real inputs.
    """
    subs = subs or {}
    ureg = next(
        (q._REGISTRY for q in subs.values() if isinstance(q, pint.Quantity)),
        pint.get_application_registry(),
    )
    coerced = {
        sym: q if isinstance(q, pint.Quantity) else ureg.Quantity(q)
        for sym, q in subs.items()
    }
    return coerced, ureg

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
    subs: dict[sympy.Symbol, pint.Quantity | float] | None = None,
    output_unit: str | pint.Unit | None = None,
    **evalf_kwargs,
) -> pint.Quantity:
    """Numerical evaluation of a sympy expression with unit-aware substitutions.

    Mirrors `sympy.Expr.evalf`'s signature. Any extra keyword arguments are
    captured by Python's `**evalf_kwargs` (a standard mechanism for
    collecting unmatched kwargs into a dict) and forwarded verbatim to
    `expr.evalf(...)`, so `n`, `maxn`, `chop`, `strict`, `quad`, and
    `verbose` all work without being listed here individually.

    Args:
        expr (sympy.Expr): The sympy expression to evaluate. Equations are
            not accepted here; use `sym_evalf` for a `sympy.Equality`, or solve
            it first and pass the resulting expression.
        subs (dict[sympy.Symbol, pint.Quantity] | None): Mapping from
            `sympy.Symbol` to `pint.Quantity` (a plain number is accepted and treated as dimensionless). Same shape as sympy.evalf's `subs` kwarg, but values
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
    subs, target_ureg = _coerce_subs(subs)
    if isinstance(expr, sympy.Equality):
        raise TypeError(
            "quantity_evalf evaluates a bare expression, not an equation. "
            "Use sym_evalf for a sympy.Equality (it infers the output symbol), or "
            "solve first: sympy.solve(eq, unknown)[0].quantity_evalf(...)."
        )
    base_subs = {sym: _quantity_to_sympy_base(q) for sym, q in subs.items()}
    unit_symbols = set().union(
        *(
            v.free_symbols
            for v in base_subs.values()
            if isinstance(v, sympy.Expr)
        ),
        set(),
    )
    collisions = unit_symbols & (expr.free_symbols | set(base_subs))
    if collisions:
        names = ", ".join(sorted(str(s) for s in collisions))
        raise ValueError(
            f"Input symbol(s) {names} have the same name as an SI base unit "
            "used in the evaluation, which would corrupt the substitution. "
            "Rename the symbol(s)."
        )
    result_value = expr.evalf(subs=base_subs, **evalf_kwargs)
    output_quantity = target_ureg(f"{result_value}")
    if output_unit is not None:
        output_quantity = output_quantity.to(output_unit)
    return output_quantity

def _to_coherent_si(quantity: pint.Quantity) -> pint.Quantity:
    """Convert a quantity to its coherent SI equivalent (kN -> N, MPa -> Pa, mm -> m, km/h -> m/s).

    Two steps per unit. First drop any SI prefix, so kN becomes N and MPa
    becomes Pa. Then, if what remains is not a coherent SI unit, expand it to
    SI base units: hour becomes second, litre becomes m^3, gram becomes
    kilogram. Coherence is read off the conversion factor to base units: it is
    exactly 1 for a coherent unit (pascal -> 1 kg/(m s^2)) and something else
    otherwise (hour -> 3600 s).

    Without the second step a speed in km/h would render as m/h, a unit no one
    uses. `kg` needs no special case here because it is already coherent.
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
        in_base = ureg.Quantity(1, base).to_base_units()
        if abs(in_base.magnitude - 1.0) > 1e-12:
            # Not coherent (hour, litre, gram): take its SI base expansion.
            for base_name, base_exponent in dict(in_base.units._units).items():
                target[base_name] = (
                    target.get(base_name, 0) + base_exponent * exponent
                )
        else:
            target[base] = target.get(base, 0) + exponent
    return quantity.to("*".join(f"{n}**{e}" for n, e in target.items()))

def _sig_fig_decimal(value: float, n_display: int) -> Decimal:
    """Round `value` to `n_display` significant figures, as a `Decimal`.

    `Decimal` keeps trailing zeros as significance (500 at 4 significant
    figures is `500.0`) and its `to_eng_string` provides engineering notation
    (exponent a multiple of 3), so the stdlib does the digit bookkeeping.
    """
    return Decimal(f"{float(value):.{n_display - 1}e}")

def _format_quantity(
    quantity: pint.Quantity,
    n_display: int,
    *,
    engineering: bool,
    trim: bool,
) -> str:
    """Format a pint quantity as a LaTeX `magnitude + unit` string.

    The magnitude is rounded to `n_display` significant figures. With
    `engineering` True it renders as engineering notation (mantissa times a
    power of ten that is a multiple of 3) when an exponent is needed; `trim`
    drops trailing zeros (and a dangling decimal point), so a clean value
    like 500 renders as `500`, not `500.0`.

    Rounding to significant figures also rounds away pint's float-based
    conversion noise (100 mm^2 becomes 1e-4 m^2, not 9.999e-5).
    """
    magnitude = _sig_fig_decimal(quantity.magnitude, n_display)
    if engineering:
        eng = magnitude.to_eng_string()
        mantissa, has_exp, exponent = eng.partition("E")
        mag_str = (
            rf"{mantissa}\times 10^{{{int(exponent)}}}" if has_exp else eng
        )
    else:
        mag_str = format(magnitude, "f")
        if trim and "." in mag_str:
            mag_str = mag_str.rstrip("0").rstrip(".")
    unit_latex = f"{quantity.units:~L}"
    return f"{mag_str}\\ {unit_latex}" if unit_latex else mag_str

def _coherent_si(quantity: pint.Quantity) -> "tuple[pint.Quantity, bool]":
    """Return `(quantity in coherent SI units, whether that changed the unit)`.

    The flag drives the engineering-notation choice: a unit that carried an SI
    prefix (kN, mm, MPa) or was not coherent (km/h, L) reads better in
    engineering form once converted. Centralised here so the substituted SI
    line and the result-line dual ask the question in one place.
    """
    converted = _to_coherent_si(quantity)
    return converted, converted.units != quantity.units

def _format_substituted_value(
    quantity: pint.Quantity,
    n_display: int,
    *,
    si_form: bool = False,
) -> str:
    """Format one input value for the substituted form.

    Substituted inputs show one more significant figure than the result
    (`n_display + 1`), trailing zeros trimmed. With `si_form` True the value
    is shown in coherent SI units, in engineering notation when the conversion
    changed the unit.
    """
    if si_form:
        shown, engineering = _coherent_si(quantity)
    else:
        shown, engineering = quantity, False
    return _format_quantity(
        shown, n_display + 1, engineering=engineering, trim=not engineering
    )

def _format_result(
    quantity: pint.Quantity,
    n_display: int,
) -> "tuple[str, str]":
    """Format the result line, returning `(value_latex, dual_latex)`.

    `value_latex` is the quantity at exactly `n_display` significant figures
    in its own unit, trailing zeros kept: they carry the precision claim.
    `dual_latex` prepends a coherent-SI engineering form (`eng = value`) when
    the unit is not already coherent SI, otherwise it equals `value_latex`.
    """
    value_latex = _format_quantity(quantity, n_display, engineering=False, trim=False)
    converted, changed = _coherent_si(quantity)
    if changed:
        eng = _format_quantity(converted, n_display, engineering=True, trim=False)
        return value_latex, f"{eng} = {value_latex}"
    return value_latex, value_latex

def _render_substituted(
    expr: sympy.Expr,
    subs: dict[sympy.Symbol, pint.Quantity],
    n_display: int,
    *,
    si_form: bool = False,
) -> str:
    """Render the substituted form: `expr` with each input symbol replaced by its formatted value and unit.

    The placeholder trick lives here, in one place. Each input symbol is
    swapped for a unique `SymEvalPH#Z` symbol so sympy renders the structure
    without simplifying (``a + a`` stays ``a + a``) or dropping units; each
    placeholder is then spliced back to a formatted `value + unit` string. The
    trailing "Z" keeps the substring replace safe: `SymEvalPH0Z` never matches
    inside `SymEvalPH10Z`. Placeholder indices follow the canonical sort order
    of the input symbols, so sympy.Mul ordering matches the symbolic form.

    With `si_form` True, each quantity is converted to its coherent SI form
    (kN -> N, mm -> m, km/h -> m/s) and shown in engineering notation when
    that conversion changed its unit; this is the extra line rendered in
    verbose mode.

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
            quantity, n_display, si_form=si_form
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
    """Arrange a working as a stacked LaTeX `aligned` block.

    Uses `aligned`, not `align*`: `aligned` is an inner environment, legal
    inside `$...$` and `$$...$$`, so `.latex` renders wherever it is dropped
    (marimo, Jupyter, Quarto). `align*` is an outer environment that KaTeX
    (and strictly MathJax) reject when nested. Includes the SI-base
    substituted line when the working carries one (verbose).
    """
    lines = [
        rf"{working.symbol} &= {working.symbolic} \\",
        rf"&= {working.substituted} \\",
    ]
    if working.si_substituted is not None:
        lines.append(rf"&= {working.si_substituted} \\")
    lines.append(rf"{working.symbol} &= {working.result_dual}")
    return "\\begin{aligned}\n" + "\n".join(lines) + "\n\\end{aligned}"

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
        # Inline `$...$`, not display `$$...$$`, so the evaluation renders
        # left-justified when dropped into a marimo/Jupyter layout (display
        # math is centered by the host CSS). `\displaystyle` restores the full
        # size that inline math would otherwise shrink.
        return rf"$\displaystyle {self.latex}$"

    def __repr__(self):
        return f"SymbolicEvaluation({self.quantity!r})"

    def __str__(self):
        return str(self.quantity)

def sym_evalf(
    expr: "sympy.Expr | sympy.Equality",
    subs: dict[sympy.Symbol, pint.Quantity | float] | None = None,
    output_unit: str | pint.Unit | None = None,
    *,
    n_display: int = 4,
    mode: Literal["multi_line", "verbose", "one_line"] = "multi_line",
    output_symbol: str | sympy.Symbol | None = None,
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
            `sympy.Symbol` to `pint.Quantity` (a plain number is accepted and treated as dimensionless). Same shape as sympy.evalf's `subs` kwarg. Defaults to
            None (no substitutions).
        output_unit (str | pint.Unit | None): Target pint unit for the
            result. If `None`, the result is rendered in SI base units.
            Defaults to None.
        n_display (int): Significant figures for the result; substituted
            inputs show one more figure, with trailing zeros trimmed.
            Defaults to 4. Display only: it never changes the computed
            quantity. Numeric precision is sympy's `n` (15 significant
            digits by default); a warning is raised when `n < n_display`,
            because the extra displayed digits would be meaningless.
        mode (Literal["multi_line", "verbose", "one_line"]): Rendering
            style, defaults to `"multi_line"`:

            - `"multi_line"`: three lines: symbolic form, substituted form with
              units, then result.
            - `"verbose"`: four lines: multi_line plus an extra
              substituted form in SI base units, in engineering notation.
            - `"one_line"`: a single line,
              `symbol = symbolic form = substituted form = result`, with just the
              variable's unit on the right (no prefix-stripped dual).
        output_symbol (str | sympy.Symbol | None): LaTeX label for the
            output: a string like `r"\\sigma"` or a `sympy.Symbol`. The label
            appears to the left of the symbolic form and of the result;
            the substituted lines carry no label.
            Required for a bare expression; for an equation it
            defaults to the inferred unknown, and an explicit value overrides
            only the rendered label.
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
    n_precision = evalf_kwargs.get("n", 15)
    if n_precision < n_display:
        warnings.warn(
            f"n={n_precision} significant digits are computed, but "
            f"n_display={n_display} are shown; displayed digits beyond the "
            "computed precision are meaningless. Raise n or lower n_display.",
            stacklevel=2,
        )
    subs, _ = _coerce_subs(subs)
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

    substituted_latex = _render_substituted(expr, subs, n_display)

    si_substituted_latex = (
        _render_substituted(expr, subs, n_display, si_form=True)
        if wants_si
        else None
    )

    output_quantity = quantity_evalf(
        expr, subs=subs, output_unit=output_unit, **evalf_kwargs
    )

    output_var_unit_latex, output_dual_latex = _format_result(
        output_quantity, n_display
    )

    if isinstance(output_symbol, sympy.Symbol):
        output_sym = output_symbol
    else:
        output_sym = sympy.Symbol(str(output_symbol))
    sym_latex = sympy.latex(output_sym)
    # `full_latex` is the BARE LaTeX (no `$` delimiters, no `\displaystyle`).
    # SymbolicEvaluation._repr_latex_ wraps it as inline `$\displaystyle ...$`
    # for a left-justified default render. Callers embedding the math elsewhere
    # wrap `result.latex` themselves: `$\displaystyle {...}$` for a
    # left-justified inline block, `$${...}$$` for a centered display block.
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
