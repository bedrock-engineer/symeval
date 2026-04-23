# symeval

## Idea
The idea is to build something like handcalcs and Calcpad, but then for in marimo notebooks using sympy symbolic math formulas as a starting point, such that we can create explorable explanations in marimo notebooks.

.symeval() should become a method that you can call on a sympy expression, i.e. the symeval package extends sympy's expression API with the symeval method. The symeval method substitutes numbers with units into the expression and not only renders the final numerical result, but also the intermediate results, which contains the formula with the filled in numbers.

## Inspiration
- handcalcs: [GitHub](https://github.com/connorferster/handcalcs)
- Calcpad: [Website](https://calcpad-ce.org); [Docs](https://imartincei.github.io/CalcpadCE); [GitHub](https://github.com/imartincei/CalcpadCE)
- sympy: [Website](https://worrydream.com/ExplorableExplanations/); [Docs](https://docs.sympy.org/latest/index.html); [GitHub](https://github.com/sympy/sympy)
- [Explorable Explanations](https://worrydream.com/ExplorableExplanations/)

## Project plan
Take the `axial_resistance_of_steel_hss_member.py` marimo notebook as a starting point, and build a Python package from that notebook using [`mobuild`](https://github.com/koaning/mobuild).
The [`hastyplot`](https://github.com/koaning/hastyplot) repo can be used as an example of how to build a package using `mobuild`.

