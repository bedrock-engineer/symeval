# Issue draft → `marimo-team/marimo` (islands runtime; observed via quarto-marimo)

**Title:** Islands render `mo.ui.table` selection state and `mo.ui.radio`
orientation with lower fidelity than the marimo app

(Note before filing: the screenshot links below are Discord CDN URLs and
expire; re-capture and attach them to the issue directly.)

---

## Summary

Two `mo.ui` elements render differently on an islands page (quarto-marimo)
than in the running marimo notebook, both on quarto-marimo `0.4.5` and
`0.5.0`.

## Environment

- marimo `0.24.0`
- quarto-marimo `0.4.5` and `0.5.0`
- Quarto `1.10.18`, Linux (WSL2), Chromium

## 1. `mo.ui.table`: the selected row is hard to see

On `0.4.5` the selected row is highlighted, but its checkbox is not checked:

![The selected row checkbox is not checked](https://cdn.discordapp.com/attachments/1531753847293214740/1531951125107052727/image.png?ex=6a9a8a2a&is=6a9938aa&hm=77ff4a4d217475d63fbc4a0e8c0bcc6dd0202a9f60e11bc6fc7a084e0b632662&)

On `0.5.0` it flips: the selected row's checkbox now carries the checked state
(`data-state="checked"`) and draws a checkmark, but it renders as a barely
visible light-grey check with no accent background, and the row highlight
and the hover highlight are gone. In the marimo app the selected row shows
both a clearly checked (accent-filled) checkbox and a highlighted row.

Live example: https://bedrock-engineer.github.io/symeval/getting-started.html#quantity_evalf-on-a-dataframe

## 2. `mo.ui.radio` renders horizontally

The "P V T n" radio group renders horizontally on the islands page, instead of
vertically as in the marimo notebook (unchanged between `0.4.5` and `0.5.0`):

![Radio is horizontal instead of vertical like in the marimo notebook](https://cdn.discordapp.com/attachments/1531753847293214740/1531951125429747792/image.png?ex=6a9a8a2a&is=6a9938aa&hm=027e35ab19e27ea328b090c9a49ec5f1830202c553b5bfab948ed4091ede68dd&)

Live example: https://bedrock-engineer.github.io/symeval/getting-started.html#ideal-gas-law

## Expected

Islands render `mo.ui` elements with the same visual state and layout as the
marimo app: a clearly checked checkbox plus row highlight for table selection,
and a vertical radio group.
