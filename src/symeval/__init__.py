__all__ = ['ureg', 'Q_', 'Variable', 'symeval']


import textwrap
from dataclasses import dataclass, field

import pint
import sympy
from sympy import latex

# Default unit registry with sensible defaults for engineering calculations
ureg = pint.UnitRegistry(auto_reduce_dimensions=True)
ureg.formatter.default_format = "~L"
Q_ = ureg.Quantity

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
