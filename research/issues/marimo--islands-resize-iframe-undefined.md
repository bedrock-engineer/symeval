# Issue draft → `marimo-team/marimo` (islands runtime; observed via quarto-marimo)

**Title:** `mo.iframe` output calls `__resizeIframe(this)` in `onload`, but the
islands runtime never defines it, so every load logs a `ReferenceError`

---

## Summary

`mo.iframe(...)`'s serialized output sets `onload="__resizeIframe(this)"` on
the iframe. In the marimo app that helper exists; on an islands page
(quarto-marimo) nothing defines it, so the browser console logs

```
ReferenceError: __resizeIframe is not defined
```

every time the iframe loads (once for the pre-hydration static snapshot, again
for the hydrated render). The iframe itself still displays, but auto-resizing
presumably never happens and the console noise flags every page load.

## Environment

- marimo `0.24.0`
- quarto-marimo `0.4.5` and `0.5.0` (identical on both)
- Quarto `1.10.18`, Linux (WSL2), Chromium

## Reproduction

Any islands page with a cell whose output is `mo.iframe(...)`. Live example
(the piston animation): https://bedrock-engineer.github.io/symeval/getting-started.html
(open the console and reload).

## Expected

The islands runtime defines the same `__resizeIframe` helper the app provides
(or the serialized output omits the `onload` when the helper is absent).
