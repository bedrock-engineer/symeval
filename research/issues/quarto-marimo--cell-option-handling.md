# Issue draft → `marimo-team/quarto-marimo`

**Title:** Cell options: header-level options never reach the cells,
`code-fold` is a no-op, `hide-code` drops the source

---

## Status history

Drafted against `0.4.5`, where `#| editor` was dead and `#| echo: true` showed
the code together with the editor. **Fixed in `0.5.0`:** `#| echo: true`
renders a read-only code block, `#| editor: true` a single live editor.

Re-tested 2026-10-04 on `0.5.0` with marimo `0.25.1`, Quarto `1.10.18` and
`1.9.37` (identical results). Three gaps remain, each with a fix in
[bedrock-engineer/quarto-marimo](https://github.com/bedrock-engineer/quarto-marimo)
that can be offered as a PR.

## 1. Options in the YAML header never reach the cells

`echo: true`, `error: false` or `code-fold: true` in a document's header have
no effect. `execution_options_patch` maps them, but it receives them through
`page_options_from_root`, the attributes of the root element built by marimo's
markdown parser, which copies a frontmatter key only when its value is a string
(`marimo/_convert/markdown/to_ir.py`: `if isinstance(value, str):
parent.set(key, value)`). A YAML boolean never arrives. The quoted form
(`echo: "true"`) does not help: Quarto's YAML validation rejects it ("must
instead be `true` or `false`"). The one header option that works, `eval:
false`, works because the TypeScript engine reads it from Quarto's metadata.

Evidence (0.5.0): with `echo: true` in the header, every island payload still
has `render.source: false`. With `error: false` in the header, a page whose cell
raises `ModuleNotFoundError` renders with exit 0; the same option per cell
(`#| error: false`) fails the render with `RuntimeError: marimo execution
failed`.

Fix: read the header once with marimo's own `extract_frontmatter` in
`convert_markdown` and hand it to `collect_page`, so the root only supplies the
cells (branch `fix/document-options`, 97 insertions, 21 deletions, tested on
marimo 0.23.16 and 0.25.1).

## 2. `code-fold` and `code-summary` are silently dropped

Neither is a recognized option, and Quarto's own folding cannot reach the code
because `#| echo: true` emits it as raw `<pre><code>` HTML inside the island's
server output: no highlighting, no copy button, nothing for `code-fold` to key
on. Verified with one cell per option (`quarto-marimo--cell-options-test.qmd`)
and the decoded island payloads: `code-fold` does not even reach the cell's
`options`.

Fix: carry the source as data (`authorSource`) and let the projection emit a
real Pandoc code block with `.cell-code` ahead of the island, so Quarto
highlights, folds and copies it natively; `code-fold` implies `echo: true`
(branch `feat/author-source-code-blocks`).

## 3. `hide-code` should fold, not remove

In the marimo app a `hide_code` cell's code is collapsed but revealable. The
`hide_code="true"` fence attribute the exporter emits maps to `hide-code`,
which behaves as `echo: false`: the code is gone from the page. The faithful
mapping is a fold.

Fix: map `hide-code` to `code-fold: true`; `#| code-fold: false` restores the
old reading per cell; formats that cannot fold, such as PDF, keep omitting the
source (branch `feat/hide-code-folds`). With #108's `interactive: false`, a
static HTML page folds as well.

## 4. No per-cell static-vs-reactive marker

All executed cells become reactive islands. #108 and #110 cover the page
level; a `#| reactive: false` cell option, rendering the build-time output as
static HTML and leaving the cell out of hydration, would cover a tutorial whose
intro example should be static while later widgets stay live. `#| eval: false`
and `#| disabled: true` skip execution, which is not the same thing.
