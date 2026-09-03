# Issue draft → `marimo-team/marimo` (islands runtime; observed via quarto-marimo)

**Title:** Islands hydration renders a `mo.ui.code_editor` output twice: the
static snapshot is not removed when the hydrated output is mounted

---

## Summary

On a page of reactive islands, a cell whose output is a `mo.ui.code_editor`
ends up rendered **twice** after the islands runtime hydrates: once as the
freshly hydrated output, and once as the pre-hydration static snapshot, which
is left in the DOM instead of being removed or replaced. Every other UI
element on the same page (sliders, radio, table) hydrates cleanly with no
duplicate.

## Environment

- marimo `0.24.0`
- quarto-marimo `0.4.5` (reproduces identically on `0.5.0`)
- Quarto `1.10.18`, Python 3.13, Linux (WSL2)
- Chromium (Playwright)

## Reproduction

1. A notebook cell (hidden code) whose output is a code editor:

   ```python
   piston_js_editor = mo.ui.code_editor(
       value=initial_js_str,
       language="javascript",
       debounce=True,
       label="Piston JavaScript",
   )
   piston_js_editor
   ```

2. Render the page via quarto-marimo, so the cell becomes a reactive island.
   The static export contains the expected single snapshot:

   ```html
   <marimo-island data-app-id="main" data-cell-id="ROlb" data-reactive="true">
     <marimo-cell-output>
       <marimo-ui-element object-id="ROlb-0" ...><marimo-code-editor ...>
     ...
   ```

3. Open the page and let the islands runtime hydrate.

**Actual:** the island now contains the UI element `ROlb-0` **twice**: the
hydrated render (inside the runtime's `div.relative.min-h-6` output mount) and
the original static `<marimo-ui-element>` snapshot as a sibling. The user sees
two stacked, fully functional code editors.

```text
querySelectorAll over the hydrated page (piercing shadow roots):
  marimo-code-editor count: 2
  duplicated ui object-ids: {"ROlb-0": 2}
```

**Expected:** one code editor; the static snapshot is removed when the
hydrated output mounts, as happens for every other element kind on the page.

## Impact

Any docs page that shows a code editor widget displays it twice. With a large
editor value (an embedded script), the duplicate dominates the page.

## Workaround

Strip the code-editor cell from the static export and substitute its
`.value` reference with the initial value, losing the interactive editor on
the exported page.

## Note

Reproduced on the SymEval getting-started page
(`bedrock-engineer/symeval`, `docs/getting-started.qmd`, generated from
`examples/getting_started.py`). The same page's sliders, radio group, and
table hydrate without duplicates, so this looks specific to
`mo.ui.code_editor` (or to elements whose snapshot is a custom element with a
CodeMirror mount) rather than a general snapshot-removal failure.
