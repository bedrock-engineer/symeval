# Issue draft → `marimo-team/marimo`

**Title:** `mo.iframe` strips newlines in its HTML serialization (`.text`), breaking embedded `<script>` with `//` comments — fine live, blank when exported

---

## Summary

`mo.iframe(html)` removes newlines from `html` when serializing the iframe
`srcdoc` to HTML. Any embedded `<script>` that relies on newlines — most
commonly `//` line comments — is corrupted: the comment swallows the rest of the
(now single-line) script, so the script silently does nothing.

Crucially this is in the **HTML serialization** (`.text` / the representation
used for static export and islands), **not** the live render: the iframe
**works in the running marimo app** but is **blank when the notebook is exported
or rendered statically** (e.g. via `quarto-marimo` or `marimo export html`).

## Environment

- marimo `0.23.14`; still reproduces on `0.24.0` via the static/session export
  path (`marimo export session`, quarto-marimo islands). On `0.24.0` the
  live-kernel `.text` path serves the iframe from a virtual file
  (`src='./@file/...'`) with newlines intact, but exports still collapse the
  `srcdoc` to one line.
- Python 3.13, Linux (WSL2)

## Reproduction

```python
import marimo as mo

h = mo.iframe("<div>A</div>\n<script>\n// c\nconsole.log('x');\n</script>", height="60px")
print(h.text)
```

**Actual output:**

```html
<iframe srcdoc='&lt;div&gt;A&lt;/div&gt;&lt;script&gt;// cconsole.log(&#x27;x&#x27;);&lt;/script&gt;' ...></iframe>
```

Note `// cconsole.log(...)` — the newline between the comment and the statement
is gone, so `console.log('x')` is commented out and never runs.

**Expected:** newlines inside the HTML (and especially inside `<script>`) are
preserved, so the embedded JS runs as written.

## Impact

Any `mo.iframe` whose HTML contains a `<script>` with `//` comments (or any
newline-significant JS) renders blank / non-functional. A concrete case: a
`<canvas>` animation whose setup script begins with `// …` comments never draws.

## Workaround

Use `/* … */` block comments and semicolon-terminate every statement, so the
script survives being collapsed onto one line. But this is fragile; preserving
newlines in the `srcdoc` is the real fix.

## Where it lives

The stripping is `flatten_string` (`marimo/_output/utils.py`), which
`mo.iframe`'s serialization wraps around the whole `h.iframe(...)` element in
`marimo/_output/formatting.py` — flattening the element also flattens the
`srcdoc` payload inside it.

## Note

This reproduces with plain marimo via `.text` (above), independent of Quarto —
the stripping is in `mo.iframe`'s HTML serialization, which is the path static
exporters (`quarto-marimo`, `marimo export html`) consume. The live notebook
uses a different render path and is unaffected, which is why the problem only
appears in exported / rendered HTML.
