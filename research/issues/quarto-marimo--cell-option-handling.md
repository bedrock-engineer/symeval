# Issue draft → `marimo-team/quarto-marimo`

**Title:** Cell options `editor` and `code-fold` are no-ops; no way to show read-only code (without the editor)

---

## Summary

Reading the render path in `_extensions/marimo-team/marimo/extract.py` (0.4.5),
several documented / expected cell options do not take effect:

1. **`editor` is a no-op.** `default_config` includes `"editor": False`, but
   `editor` is never read in the render path. `get_mime_render` only forwards
   `echo` (as `display_code`) and `eval` (as `reactive` / `is_reactive`) to
   `stub.render(...)`. So `#| editor: true` does nothing — even though the
   [quarto-marimo home page](https://marimo-team.github.io/quarto-marimo/index.html)
   documents an `editor` option.
2. **`code-fold` is unsupported.** It is not in `default_config` and not
   referenced anywhere, so `#| code-fold: true` does nothing (Quarto's native
   code folding does not apply to the rendered islands).
3. **No "read-only code" display.** `#| echo: true` shows the code, but
   (observed) it appears *together with* the interactive editor; there is no way
   to show read-only code on its own. The option that would presumably control
   this, `editor`, is the dead one in (1). (Note: `echo` itself works both ways —
   `#| echo: false` correctly hides the code and simply matches the default;
   that is expected, not a bug.)

## Environment

- quarto-marimo extension `0.4.5`
- marimo `0.23.14`
- Quarto `1.9.38`
- Linux (WSL2)

## Where in the source

`extract.py`:

```python
default_config = {
    "eval": True,
    "echo": False,
    "output": True,
    "error": True,
    "include": True,
    "editor": False,   # <- declared, but never consumed in the render path
}
```

```python
render_options = {
    "display_code": config["echo"],
    "reactive": eval_enabled and not mime_sensitive,
}
# ...
stub.render(display_code=config["echo"], is_reactive=bool(render_options["reactive"]))
# `config["editor"]` and any `code-fold` are not passed through.
```

## Reproduction

A minimal doc with one `{python .marimo}` cell per option
(`#| echo: true`, `#| echo: false`, `#| editor: true`, `#| code-fold: true`)
renders identically regardless of `editor` / `code-fold`, and only `echo: true`
changes whether code is shown. (Minimal `opts.qmd` can be attached.)

## Expected / suggestion

- Make `editor` and `code-fold` behave as documented, **or** remove them from
  `default_config` / the docs to avoid implying they work.
- Consider a clear separation between "show code (read-only)" and "show editor",
  since the current single `echo` knob plus a reactive island tends to surface
  both together.
