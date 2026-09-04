"""Cut a release: bump the version, commit, tag, push, create the GitHub release.

Invoked by `uv run task release <version>`. Taskipy's `pre_release` hook has
already run `build`, `test` and `docs_readme` by the time this starts.

This is a Python script rather than a shell one-liner in `pyproject.toml` so it
works the same on Windows (where taskipy hands the task body to `cmd.exe`, which
does not understand POSIX quoting) as on Linux and macOS.

See RELEASING.md for the full flow.
"""

from __future__ import annotations

import subprocess
import sys


def run(*cmd: str) -> None:
    """Run a command, aborting the release if it fails."""
    print(f"$ {' '.join(cmd)}", flush=True)
    if subprocess.run(cmd).returncode != 0:
        sys.exit(f"release aborted: {' '.join(cmd)} failed")


def main() -> None:
    if len(sys.argv) != 2:
        sys.exit("Usage: uv run task release <version>")
    version = sys.argv[1]

    # A dirty tree usually means a stale generated file (`__init__.py`, README)
    # that pre_release just rewrote: commit it and re-run.
    if subprocess.run(("git", "diff", "--quiet", "HEAD")).returncode != 0:
        sys.exit("release aborted: working tree not clean")

    run("uv", "version", version)
    run("git", "commit", "-m", f"Release {version}", "pyproject.toml", "uv.lock")
    run("git", "tag", version)
    run("git", "push")
    run("git", "push", "--tags")
    run("gh", "release", "create", version, "--generate-notes")


if __name__ == "__main__":
    main()
