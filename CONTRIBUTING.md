# Contributing to SymEval

Thanks for considering a contribution. This guide covers the development setup,
running the tests, previewing the docs site, and adding a worked example. For the
deeper project layout see [`AGENTS.md`](AGENTS.md), and for cutting a release see
[`RELEASING.md`](RELEASING.md).

## Setup

SymEval uses [uv](https://docs.astral.sh/uv/). Install the development
dependencies:

```sh
uv sync --group dev      # taskipy, pytest, marimo, polars
```

Tasks are defined under `[tool.taskipy.tasks]` in `pyproject.toml` and run with
`uv run task <name>`. That table is the source of truth; list every task, with
its command body, at any time:

```sh
uv run task -l
```

## The source of truth

Almost everything lives in **`symeval_mo.py`**, a single marimo notebook laid out
in three columns: the worked examples, the library implementation (cells marked
`## EXPORT`), and the tests. Two files are generated from it and should **not** be
edited by hand:

- `src/symeval/__init__.py` — the package, produced by `uv run task build`.
- `examples/getting_started.py` — the tutorial notebook, produced by
  `uv run task docs` (it extracts the examples column).

To change library behaviour, a test, or the tutorial, edit `symeval_mo.py` (open
it with `uvx marimo edit symeval_mo.py`), then regenerate.

## Tests

```sh
uv run task test         # pytest against symeval_mo.py
```

Test functions are the `def test_*` cells in the notebook's test column.

## Docs site

The docs site is a [Quarto](https://quarto.org) project in `docs/`, built with
the [quarto-marimo](https://github.com/marimo-team/quarto-marimo) extension.
Quarto ships as the `quarto-cli` wheel, so the whole toolchain installs through
uv, no system install needed:

```sh
uv sync --group docs     # quarto-cli, marimo, polars
```

Run the live-reloading dev server:

```sh
uv run task docs_preview  # quarto preview docs/
```

The pages are generated from `.py` notebooks, so the edit loop depends on what
you change:

- **Prose pages** (`docs/index.qmd`, `docs/explanation.qmd`, `docs/reference.qmd`):
  edit and save. The preview hot-reloads immediately.
- **Notebook pages** (from `symeval_mo.py` or `examples/*.py`): run
  `uv run task docs` in another terminal to regenerate the `.qmd`. The preview
  watches the `.qmd` files and refreshes when they change.

To render the static site once (what CI deploys):

```sh
uv run task docs_render   # -> docs/_site/
```

## Adding a worked example

Worked examples are standalone marimo notebooks in `examples/`. To add one:

1. Author the notebook as `examples/<name>.py` (snake_case), for example with
   `uvx marimo edit examples/<name>.py`. Give it a PEP 723 header listing its
   dependencies (at least `marimo` and `symeval`).
2. Run `uv run task docs`. This renders it to `docs/examples/<name-kebab>.qmd`
   (snake_case file, kebab-case URL), rewrites the marimo cells into the
   extension's `python {.marimo}` syntax, and adds an *Open in molab* badge.
   The page is picked up automatically by the render globs in `docs/_quarto.yml`.
3. Add it to the sidebar: the sidebar in `docs/_quarto.yml` is curated by hand,
   so add an entry under the `Examples` section pointing at the new page.
4. Preview with `uv run task docs_preview` to check it renders and runs.
5. Commit both the `.py` and the generated `.qmd`.

The molab badge points at the notebook on the `main` branch, so it goes live once
your change merges.

## Opening a pull request

Branch off `main`, keep changes focused, and open a pull request. If you touched
`symeval_mo.py`, make sure `uv run task build` and `uv run task test` were run so
the generated package and the tests stay in sync. Releases are maintainer-only;
see [`RELEASING.md`](RELEASING.md).
