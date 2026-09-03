# Issue draft → `marimo-team/quarto-marimo`

**Title:** Cell option gaps remaining in 0.5.0: `code-fold` is a no-op, and no
per-cell static-vs-reactive marker

---

## Status history

Originally drafted against `0.4.5`, where `#| editor` was a declared-but-dead
option and `#| echo: true` showed the code *together with* the interactive
editor, with no way to show read-only code on its own.

**Fixed in `0.5.0`** (verified in `python/quarto_marimo/authoring.py` and
`compiler.py`): `#| echo: true` now renders a read-only code block without the
editor (`renders_author_source` renders plain source unless `editor` is also
true), and `#| editor: true` works as documented (implies showing the source,
as an editor). The recognized per-cell options are now: `echo`, `editor`,
`output`, `server-output`, `error`, `include`, `eval`, `disabled`,
`unparsable`, `hide-code`, `hide-output`, `name`, `column`.

The two gaps below remain on `0.5.0`.

## Environment

- quarto-marimo extension `0.5.0` (also `0.4.5`)
- marimo `0.24.0`
- Quarto `1.10.18`
- Linux (WSL2)

## 1. `code-fold` is unsupported

`#| code-fold: true` does nothing: it is not among the recognized render
options, and Quarto's native code folding does not apply to the rendered
islands. There is no way to make a cell's code collapsible. (Our workaround:
the docs generator wraps the code in a manual `<details>` block.)

Verified empirically on `0.5.0` with a test page
(`quarto-marimo--cell-options-test.qmd`, one cell per option, decoded the
`data-marimo-payload` and probed the hydrated page):

- `#| code-fold: true` and `#| code-summary` are silently dropped; they do not
  even reach the cell's `options` in the island payload. Alone, `code-fold`
  shows no code; combined with `#| echo: true` the code shows unfolded.
- `#| echo: true` works as documented: a read-only code block above the
  output, no editor.
- `#| editor: true` works: a single live editor with line numbers and a run
  button (no duplication; the duplicate-render bug is specific to
  `mo.ui.code_editor` *outputs*).
- The `hide_code="true"` fence attribute that `marimo export md --flavor qmd`
  emits maps (via the `_` → `-` attribute rewrite) to `hide-code`, which
  behaves exactly like `#| echo: false`: the code is gone.

### `hide-code` should fold, not remove

In the marimo app, a `hide_code` cell's code is *collapsed but revealable* —
the reader can always open it. Mapping `hide-code` to `echo: false` on the
rendered page silently drops that half of the semantics: the code becomes
unreachable. The faithful mapping is `code-fold: true` (collapsed, expandable
code), which is also the strongest argument for supporting `code-fold` in the
first place.

## 2. No per-cell static-vs-reactive marker

All executed cells become reactive islands. There is no way to mark one cell
as "run at build time, render the static output, don't hydrate" while the rest
of the page stays reactive, e.g. a tutorial whose intro example should be
static and whose later widgets should be live. `#| eval: false` /
`#| disabled: true` skip execution entirely, which is not the same thing.

Suggestion: a `#| reactive: true / false` cell option (default true) that
renders the build-time output as static HTML and excludes the cell from
hydration.
