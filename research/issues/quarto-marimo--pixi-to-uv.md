# Issue draft → `marimo-team/quarto-marimo`

**Title:** Idea: drop pixi and run the dev toolchain on uv alone

---

**TL;DR** — Nothing left in `[tool.pixi.dependencies]` is conda-only (pandoc
comes bundled inside Quarto; deno is already a PyPI wheel here), while uv is a
hard runtime dependency of the extension. So the repo maintains two environment
managers and two lockfiles where one would do. Not a bug, nothing is broken —
close freely if you like the current setup.

## The observation

`pixi.lock` and `uv.lock` are both maintained, and CI provisions both: `lint`
uses `setup-pixi`, while `test-ts`, `test-py`, and `render` use `setup-uv`. But
as far as I can tell nothing in `[tool.pixi.dependencies]` actually needs conda:

- **pandoc** — the engine calls `quarto.system.pandoc(...)`
  (`src/engine/index.ts:205`), which per the Quarto types "runs the bundled
  pandoc binary (or `QUARTO_PANDOC` override); path to pandoc is automatically
  resolved". Nothing in `src/`, `scripts/`, or the `Makefile` invokes a bare
  `pandoc`, so `pandoc = ">=3.4,<4"` looks vestigial.
- **deno** — already a PyPI wheel in this repo: `[dependency-groups] dev =
  ["deno>=2.8"]`, resolved in `uv.lock` as `deno 2.9.4` with per-platform binary
  wheels, used as `uv run deno` in `Makefile:30`.
- **marimo, ruff, mypy, pytest, pyyaml** — all on PyPI.
- **Python itself** — uv manages interpreters.

Meanwhile uv isn't optional: `_extensions/marimo/python/command.py` turns each
document's `pyproject` front matter into `uv run` arguments via marimo's
`construct_uv_flags`, and the README asks end users to install uv. Every
contributor already has it, so pixi is the removable half of the pair.

I did notice #96 aligned the tooling across both managers only a few weeks ago,
so this may well be a deliberate choice I'm arguing against from the outside.

## Why it might be worth it

1. **One resolution instead of two that can silently disagree.** The pixi and uv
   paths don't resolve the same versions, and nothing checks that they agree.
2. **Some CI tooling isn't locked at all today.** `uv tool run --with marimo
   mypy` and `uv run --with pytest pytest` (`Makefile:32-33`) re-resolve on every
   run, so `test-py` and part of `lint` float to latest — while pixi pins
   `mypy>=2.3,<3` and `pytest>=9,<10`. Moving those into `[dependency-groups]`
   would lock them under the same resolution as everything else.
3. **Half the lock maintenance** — `pixi.lock` and `uv.lock` have each been
   touched ~13 times; one lock halves the churn and the Renovate surface.
4. **Simpler CI** — a single `setup-uv` for every job, one cache.

## What it would take

Delete `[tool.pixi.*]` and `pixi.lock`; move `ruff`, `mypy`, `pytest`, and
`pyyaml` into `[dependency-groups] dev` so they're locked; collapse the
`PIXI_PROJECT_ROOT` branch in `Makefile:22-34` to the uv arm; point the CI
`lint` job at `setup-uv`. The Makefile and the Quarto download stay exactly as
they are.

Low risk, because the uv path is already proven — three of the four CI jobs run
it today. (For a small worked example of a uv-only project of this shape, see
[bedrock-engineer/symeval](https://github.com/bedrock-engineer/symeval).)

## Trade-offs

- **Wheel provenance** — the `deno` wheel is a third-party repackaging of the
  upstream binary; conda-forge is a more curated channel and may cover
  architectures the wheels don't. (Though that wheel is already load-bearing
  here via `Makefile:30`.)
- **Onboarding** — `pixi install` is one command that yields a complete
  toolchain including the interpreter. `uv sync` is equivalent in practice, but
  only once the tools move into `[dependency-groups]`.
- **Org conventions** — if marimo-team standardizes on pixi across repos, that
  consistency may simply outweigh all of the above.

## Environment

- `marimo-team/quarto-marimo` at `30ec3af` (`main`)
- pixi `v0.76.1` (CI), uv `0.12.9`, Quarto `1.9.37` pinned

---

Happy to open a PR if it's of interest, and equally happy for this to be closed
as "we like pixi". A separate follow-up idea about the Makefile (which is what
actually blocks Windows contributors) is filed separately, and doesn't depend on
this one. Thanks for the extension either way.
