# Issue draft → `marimo-team/quarto-marimo`

**Title:** Idea: move the dev tasks from the Makefile into `pyproject.toml`
(taskipy) so the repo is workable on Windows

---

**TL;DR** — Every dev task routes through a Makefile that needs `make` plus a
POSIX shell and has no Windows branch, so a Windows contributor can't run
`lint`, `test`, or `render` (a bare `make` downloads the *Linux* Quarto
tarball). Declaring the tasks in `pyproject.toml` and running them as
`uv run task <name>` fixes that with no new tooling. Not a bug in the extension
itself — close freely.

## The observation

`[tool.pixi.tasks]` are thin wrappers over the Makefile, and the Makefile is
POSIX shell throughout. On Windows:

- `make` isn't present by default, and the recipes need `sh`, `rm -rf`,
  `find … -delete`, `mv`, `cp -R`, `curl`, `tar`.
- Platform detection (`Makefile:11-17`) branches Darwin / aarch64 /
  linux-amd64, with no Windows arm — and Git Bash reports
  `uname -s` = `MINGW64_NT-10.0`, so it falls through to **linux-amd64** there
  too.
- A bare `make` picks the default goal, which is the Quarto download target
  (`Makefile:38`), so the first thing a new contributor typing `make` gets is a
  130 MB download of Linux Quarto, followed by `tar` failing to create a symlink
  (Windows disallows that without Developer Mode). Nothing is left behind, but
  nothing works either.

Windows contributors aren't hypothetical here — #103 is an open Windows bug, and
`[tool.pixi.workspace]` already lists `win-64` among the locked platforms, so
the intent to support the platform seems to exist; it's just the task layer that
doesn't.

I did notice #96 aligned the development tooling only a few weeks ago, so this
may be arguing against a deliberate choice.

## The idea

Declare the tasks in `pyproject.toml` and run them through uv:

```toml
[tool.taskipy.tasks]
lint = "..."
test = "..."
build = "..."
render = "..."
```

```bash
uv run task lint
```

No `make`, no POSIX shell, no second task definition for the pixi path — and the
tasks are visible in `pyproject.toml` rather than in a separate file. Vincent
Warmerdam makes the general case for this nicely in
["Your pyproject.toml can be a taskrunner too"](https://www.youtube.com/watch?v=n-L2p-poGUk).
A worked example of the shape (uv + taskipy, tasks documented in
`CONTRIBUTING.md`) is
[bedrock-engineer/symeval](https://github.com/bedrock-engineer/symeval).

**Bonus:** it also lets the Quarto pin become the `quarto-cli` PyPI wheel, which
bundles the Quarto binary — replacing the curl/tar/archive-layout-sniffing
recipe entirely, i.e. the same code that needed #101. (Note the repo's current
`quarto` dependency is *not* that package — `uv.lock` has `quarto 0.1.0`, which
depends on `ipykernel`.)

This pairs naturally with the separate uv-consolidation idea, but doesn't
require it: taskipy tasks work whether or not pixi stays.

## Trade-offs

- **taskipy is dumber than make** — no file targets, no incremental rebuilds.
  Nearly every target here is already `.PHONY` and the only true file target is
  the Quarto download, so little is lost, but `docs-prepare: build` ordering has
  to be re-expressed as composite / `pre_` tasks.
- **`quarto-cli` couples the pin to that packaging's cadence.** Keeping the
  Makefile download (with a Windows arm added to the `uname` block) is a smaller
  alternative that fixes less.
- **Churn** for a platform the maintainers may not develop on. A minimal version
  of this — just adding a Windows branch and a `.DEFAULT_GOAL` to the Makefile —
  would remove the worst surprise without restructuring anything.

## Environment

- `marimo-team/quarto-marimo` at `30ec3af` (`main`)
- Windows 11, Git Bash (`MINGW64_NT-10.0`), GNU Make 4.4.1, uv `0.12.9`

---

Happy to open a PR (either the full taskipy move or just the minimal Makefile
fix), and equally happy for this to be closed. Thanks for the extension either
way.
