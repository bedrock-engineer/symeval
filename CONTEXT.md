# symeval

SymEval: symbolic, unit-aware evaluation of SymPy equations, rendered as LaTeX.
This allows you to show how you arrive at your results in the same way that you were taught in school:

1. write out the formula;
2. substitute numerical values and units (quantities);
3. write down the result.

This glossary fixes the words the library and its docs use, so the same concept is never called two things.

## Language

**Formula**:
An expression or equation handed to `sym_evalf` / `quantity_evalf` for evaluation. An equation carries one unknown that gets solved for; a bare expression is evaluated as written.
_Avoid_: target

**Symbolic evaluation**:
A unit-aware numeric evaluation of a formula, carrying its result quantity together with its LaTeX rendering: the formula, the numerical substitution of values, then the result. The `SymbolicEvaluation` object.
_Avoid_: the working, show your working, derivation, chain, the LaTeX chain, the three-step chain

**Symbolic form**:
The formula shown with symbols, before any values are put in.

**Substituted form**:
The formula shown with each symbol replaced by its value and unit, keeping the structure of the symbolic form intact.
_Avoid_: substituted line, numeric form, the line with numbers

**Result**:
The evaluated quantity with its unit, the last line.

**Chaining**:
Feeding one symbolic evaluation into a later one: referencing its result symbol when building the next equation, and pairing that symbol with its result quantity in the next evaluation's inputs.
_Avoid_: piping, threading

**Unknown**:
The single free symbol of an equation that has no value among the inputs. It is the symbol the equation is solved for.
_Avoid_: solve-for variable, the missing symbol
