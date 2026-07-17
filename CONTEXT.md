# symeval

symeval evaluates engineering formulas with unit-aware quantities and renders the working as LaTeX. This glossary fixes the words the library and its docs use, so the same concept is never called two things.

## Language

**Formula**:
An expression or equation handed to `sym_evalf` / `quantity_evalf` for evaluation. An equation carries one unknown that gets solved for; a bare expression is evaluated as written.
_Avoid_: target

**Symbolic evaluation**:
A unit-aware numeric evaluation of a formula, carrying its result quantity together with a rendering of the working. The `SymbolicEvaluation` object.

**Working**:
The multi-line rendering of a single symbolic evaluation: symbolic form, then substituted form, then result. From "show your working": the written-out steps of a calculation rather than just the answer.
_Avoid_: derivation, chain, the LaTeX chain, the three-step chain

**Symbolic form**:
The formula shown with symbols, before any values are put in.

**Substituted form**:
The formula shown with each symbol replaced by its value and unit, keeping the structure of the symbolic form intact.
_Avoid_: substituted line, numeric form, the line with numbers

**Result**:
The evaluated quantity with its unit, the last line of the working.

**Chaining**:
Feeding one symbolic evaluation into a later one: referencing its result symbol when building the next equation, and pairing that symbol with its result quantity in the next evaluation's inputs.
_Avoid_: piping, threading

**Unknown**:
The single free symbol of an equation that has no value among the inputs. It is the symbol the equation is solved for.
_Avoid_: solve-for variable, the missing symbol
