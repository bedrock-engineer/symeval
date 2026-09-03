# Issue draft → `marimo-team/quarto-marimo`

**Title:** islands-bridge CSS `overflow-x: auto` gives every output that
overhangs its line box a tiny vertical scrollbar (KaTeX display math, JSON
tree view)

---

## Summary

`islands-bridge-v0.5.0.css` sets `overflow-x: auto` on every island container:

```css
:where(.marimo-island-host) { ... overflow-x: auto }
:where(.marimo-island-host) :where(marimo-island, marimo-cell-output) { ... overflow-x: auto }
```

Per CSS, an element cannot compute `overflow-x: auto` with
`overflow-y: visible`; `overflow-y` silently computes to `auto` as well. Many
marimo outputs overhang their line boxes by a few pixels: KaTeX display math
(glyphs and struts extend past the block's height; measured `scrollHeight` 48
vs `clientHeight` 38 on a plain equation) and the JSON tree view. So each
such output becomes a scrollable box with a vertical scrollbar whose thumb is
almost as long as its track, scrolling 3–11 px.

## Environment

- quarto-marimo `0.5.0` (the rule is new in 0.5.0; `0.4.5` had no such CSS and
  no scrollbars)
- marimo `0.24.0`, Quarto `1.10.18`
- Visible with classic (non-overlay) scrollbars, e.g. Windows browsers

## Reproduction

Any islands page with a cell whose output is display math (e.g. a sympy
expression's `_repr_latex_`). On the SymEval getting-started page, 5 of 16
islands grew scrollbars: every LaTeX output plus the dict tree view.

## Expected

Wide-content protection without manufacturing vertical scrollbars. Options:
pair the rule with enough vertical padding on the scroll container to absorb
normal text/math overhang, apply `overflow-x: auto` only when content is
actually wider than the container (a measured class), or scope it to
known-wide output kinds.

## Workaround

The rules are zero-specificity (`:where`), so a site stylesheet can override
them:

```css
marimo-quarto-island.marimo-island-host,
.marimo-island-host marimo-island,
.marimo-island-host marimo-cell-output {
  overflow: visible;
}
```

(This restores the 0.4.5 behavior, at the cost of losing horizontal-scroll
protection for genuinely wide outputs.)
