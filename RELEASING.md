# Releasing SymEval

How to cut a new release of SymEval and publish it to PyPI.

```bash
uv run task release 0.#.#  # build, test & regenerate README (pre_release), bump version, commit, tag, push, create GitHub release
uv run task pypi           # clean dist/, build wheel, publish to PyPI
```

## One-time setup

1. **Sync dev deps** — `uv sync --group dev`. This installs [`taskipy`](https://github.com/illBeRoy/taskipy), the task runner that reads `[tool.taskipy.tasks]` from `pyproject.toml`.
2. **Install [`gh`](https://cli.github.com/)** — on Ubuntu/WSL: `sudo apt install gh`. Then `gh auth login`.
3. **Create a [PyPI](https://pypi.org/) account** if you don't have one. Verify that the name `symeval` is free at <https://pypi.org/project/symeval/>.
4. **Create a PyPI API token** at <https://pypi.org/manage/account/token/>. For the very first publish it has to be account-wide (project-scoped tokens can't be created for a project that doesn't exist yet).
5. Add the token to your shell rc:
   ```bash
   export UV_PUBLISH_TOKEN=pypi-AgEI...
   ```
6. **After the first publish:** go back to PyPI, generate a new token **scoped to the `symeval` project**, replace the account-wide token in your shell rc with it, and delete the account-wide token.

## Per-release flow

```bash
uv run task release 0.#.#   # build, test & regenerate README (pre_release), bump version, commit, tag, push, create GitHub release
uv run task pypi            # clean dist/, build wheel, publish to PyPI
```

That's it. Two commands.

Taskipy runs a `pre_<name>` hook before its tasks. That's how `pre_release` (build, test, and regenerate `README.md`) is automatically run before `release`.

### Before releasing (optional but recommended)

Refresh the locked dependencies and test against them, so each release is
verified against current versions while the release gate itself stays
deterministic (`pre_build`, `test`, and `docs_session` all run in the locked
project env):

```bash
uv run task upgrade         # uv sync --upgrade --all-groups
uv run task test
git commit -m "Upgrade locked dependencies" uv.lock
```

Do this before `task release`, not during: `release` requires a clean working
tree, and committing the lock records exactly which versions were tested.

### API-breaking releases: re-record the clips first

The example clips (`docs/public/*.{gif,mp4,webp}`, recorded by `media/`) show
live SymEval output, and the promo video embeds them. When the release changes
the API or the rendering, re-record them *before* releasing, against the local
package, so the release deploys prose, outputs, and clips atomically.

See [media/README.md](./media/README.md) for guidance on how to record the clip and render the promo video.


## What each command does

### `task release <version>`

1. Runs `build`, `test`, and `docs_readme` as prerequisites (via taskipy's `pre_release` hook) — regenerates `src/symeval/__init__.py` from the notebook, runs the test suite, and regenerates `README.md` (plus the docs pages) from the docs. If any fails, the release is aborted before anything is committed.
2. Checks the working tree is clean. If you have uncommitted changes (including a stale `__init__.py` from a forgotten `task build`, or a stale `README.md` from changed docs), the release aborts — commit the regenerated files and re-run.
3. `uv version <version>` — bumps the version in `pyproject.toml` *and* `uv.lock` (the lock file records the project's own version, so the two stay in sync).
4. `git commit -m "Release <version>" pyproject.toml uv.lock` — commits only those two files. Any other modified files stay uncommitted.
5. `git tag <version>` — creates an unsigned annotated tag.
6. `git push && git push --tags` — pushes the commit and the tag to GitHub.
7. `gh release create <version> --generate-notes` — creates a GitHub release using GitHub's auto-generated notes (list of merged PRs since the last tag, plus first-time contributors).

### `task pypi`

1. `rm -rf dist/` — clears any old wheels. PyPI is immutable: re-uploading a published version fails, so leftover files from past builds will break the publish.
2. `uv build` — builds the source distribution (`.tar.gz`) and wheel (`.whl`) into `dist/`.
3. `uv publish` — uploads everything in `dist/` to PyPI using `UV_PUBLISH_TOKEN`.

Tests do not run again here — they already ran in `release` before the tag was created. The tag is the trust boundary: once it exists, the code is tested.

## Versioning

[SemVer](https://semver.org/): `MAJOR.MINOR.PATCH`. No `v` prefix on tags or release titles (`0.2.0`, not `v0.2.0`).

- **PATCH** (`0.1.0` → `0.1.1`): bug fixes, no API changes.
- **MINOR** (`0.1.0` → `0.2.0`): new features, backwards-compatible.
- **MAJOR** (`0.1.0` → `1.0.0`): breaking changes. While `0.x.y`, you can break things in MINOR bumps — that's the convention for pre-1.0 packages.

The version lives only in `pyproject.toml`. There is no `symeval.__version__` — if you need it at runtime, use `importlib.metadata.version("symeval")`.

## If something goes wrong

- **`task release` failed before `git push`** — nothing was published. Fix the issue, re-run.
- **`task release` succeeded but `task pypi` failed** — the tag and GitHub release are live but PyPI has nothing. Fix the issue, re-run `uv run task pypi`. The tag is fine — it points at the right commit.
- **`task pypi` partially succeeded** (some files uploaded, some failed) — you cannot re-upload a file for an already-published version. Bump to the next patch version and re-release.
- **You published a broken version** — PyPI versions cannot be deleted, only [yanked](https://pypi.org/help/#yanked). Yank from the project's PyPI page (Manage → Releases → Options → Yank) and release a fix as the next patch version. Yanking hides the version from `pip install symeval` but keeps it installable for users who pinned it.
