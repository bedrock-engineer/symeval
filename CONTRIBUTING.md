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

### Task environments

The task bodies are terse on purpose; the reasoning lives here.

- **Most tasks run in the locked project env** (`uv run`, versions from
  `uv.lock`): deterministic, offline, and reproducible. The `uv_build`
  build-system makes `uv sync` install `symeval` itself in editable mode, so
  any task can import the current source without tricks.
- **`pre_build`** executes the whole notebook (`marimo export session`) as an
  end-to-end smoke test before `build` extracts the package with mobuild — a
  stronger guard than a static `marimo check`, which never runs a cell.
  Taskipy runs it automatically before `build`.
- **`docs_session`** snapshots the executed `getting_started.py` so its
  computed outputs (LaTeX) are available to the README generator (the `.qmd`
  export omits them). It runs `--no-sandbox` deliberately: the notebook's
  sandbox would install `symeval` from PyPI, which breaks the docs pipeline
  for any release that changes the API. The `--sandbox` header stays in the
  notebook for users and molab; the docs must document the current source.
- **`upgrade`** is the deliberate freshness step: it re-resolves the lock to
  current versions. Run it before a release, test, and commit `uv.lock` (see
  `RELEASING.md`), so the release gate stays deterministic while each release
  is tested against current dependencies.
- **`build`** runs mobuild via `uvx` — it's an external tool, not a project
  dependency.
- **`docs_readme`** is deliberately **not** part of `docs_build` (which CI
  runs); run it locally after changing the docs, then commit `README.md`.
- **`release`** wraps its body in `bash -c '…' --` so taskipy's appended
  arguments land at `$1`. Requires `bash` on PATH — present wherever git is
  (Git for Windows ships Git Bash).
- Nothing local exercises the notebooks' PEP 723 sandbox headers anymore
  (`uvx marimo edit --sandbox` for fresh contributors); that check is planned
  for CI (see `TODO.md`).

## The source of truth

Almost everything lives in **`symeval_mo.py`**, a single marimo notebook laid out
in three columns: the worked examples, the library implementation (cells marked
`## EXPORT`), and the tests. Several files are generated and should **not** be
edited by hand:

- `src/symeval/__init__.py` — the package, produced by `uv run task build`.
- `examples/getting_started.py` — the tutorial notebook, produced by
  `uv run task docs_generate` (it extracts the examples column).
- `docs/getting-started.qmd` (and `docs/examples/*.qmd`) — the docs pages, also
  from `docs_generate`.
- `README.md` — assembled from the docs by `uv run task docs_readme`; edit
  `docs/index.qmd`, `symeval_mo.py`, or `README.template.md` instead.

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
  `uv run task docs_generate` in another terminal to regenerate the `.qmd`. The
  preview watches the `.qmd` files and refreshes when they change.

To build the site once — regenerate the pages, then render — the way CI does:

```sh
uv run task docs_build    # regenerate pages + render -> docs/_site/
```

(`docs_render` renders only; `docs_build` runs `docs_generate` then `docs_render`.)

## Regenerating the README

`README.md` is a build artifact assembled from the docs, so the two stay in sync
— don't edit it by hand:

```sh
uv run task docs_readme
```

This runs `docs_generate` (refresh the pages), then `docs_session` (execute
`getting_started.py` and snapshot its computed outputs, which the `.qmd` export
drops), then `scripts/docs_to_readme.py` (fill the markers in `README.template.md`
with the docs content). It is deliberately **not** part of `docs_build`/CI —
regenerate the README locally when the docs change. The three interactive
examples show a recorded GIF instead of the live widget; the GIFs live in
`docs/public/` and are (re)recorded with the Node tooling in `media/`
(see `media/README.md`).

## Adding a worked example

Worked examples are standalone marimo notebooks in `examples/`. To add one:

1. Author the notebook as `examples/<name>.py` (snake_case), for example with
   `uvx marimo edit examples/<name>.py`. Give it a PEP 723 header listing its
   dependencies (at least `marimo` and `symeval`).
2. Run `uv run task docs_generate`. This writes `docs/examples/<name-kebab>.qmd`
   (snake_case file, kebab-case URL), rewrites the marimo cells into the
   extension's `{python .marimo}` syntax, and adds *Open in molab* badges at the
   top and bottom. The page is picked up automatically by the render globs in
   `docs/_quarto.yml`.
3. Add it to the sidebar: the sidebar in `docs/_quarto.yml` is curated by hand,
   so add an entry under the `Examples` section pointing at the new page.
4. Preview with `uv run task docs_preview` to check it renders and runs.
5. Commit both the `.py` and the generated `.qmd`.

The molab badge points at the notebook on the `main` branch, so it goes live once
your change merges.

## Opening a pull request

Branch off `main`, keep changes focused, and open a pull request. If you touched
`symeval_mo.py`, make sure `uv run task build` and `uv run task test` were run so
the generated package and the tests stay in sync; if you touched the docs or the
tutorial, run `uv run task docs_readme` so `README.md` and the pages stay in sync.
Releases are maintainer-only; see [`RELEASING.md`](RELEASING.md).
