# symeval

## Idea
The idea is to build something like [handcalcs](https://github.com/connorferster/handcalcs) and [Calcpad](https://calcpad-ce.org), but then for Python notebooks ([marimo](https://marimo.io) & [jupyter](https://jupyter.org/)) using [sympy](https://www.sympy.org/) symbolic math expressions and `pint` quantities (value + unit) as a starting point, such that we can create [Explorable Explanations](https://worrydream.com/ExplorableExplanations) in Python notebooks.

`symeval` adds two methods to a `sympy` expression that allows you to fill in `pint` quantities (value + unit). These methods are:

- `quant_evalf`: evaluate a sympy expression using `pint` units. (I don't remember why exactly, but I decided to not use sympy quantities for some reason, I think because sympy quantities can't handle things like GPa at all or intuitively **and** because `pint` units can be rendered nicely using pint's formatter "~L". Could that be?)
  This is especially useful when you want to calculate the quantities of a new column in a dataframe in a unit-aware manner.
- `sym_evalf`: evaluate a sympy expression using `pint` units **and** return the LaTeX expression of the filled in formula.

Shortly explain what's great about [handcalcs](https://github.com/connorferster/handcalcs), i.e. it's raison d'etre, here. Then shortly explain that it isn't great that it relys on Jupyter cell magic, i.e. what the disadvantages of Jupyter cell magic are (such as the inability to render variables when doing e.g. `a = x1` where `x1` was calculated in another cell). 

Advantages of using sympy:
- ability to use symbolic math with `sympy` before plugging in the numbers
- ability to apply .evalf or .quant_evalf to a dataframe of values.

## Inspiration
- handcalcs: [GitHub](https://github.com/connorferster/handcalcs)
- Calcpad: [Website](https://calcpad-ce.org); [Docs](https://imartincei.github.io/CalcpadCE); [GitHub](https://github.com/imartincei/CalcpadCE)
- sympy: [Website](https://worrydream.com/ExplorableExplanations/); [Docs](https://docs.sympy.org/latest/index.html); [GitHub](https://github.com/sympy/sympy)
- Bret Victor's [Explorable Explanations](https://worrydream.com/ExplorableExplanations/)


