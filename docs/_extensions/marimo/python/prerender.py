#!/usr/bin/env python3

"""Export a Quarto project's marimo notebooks as a pre-render step."""

from __future__ import annotations

from quarto_marimo.prerender import main

if __name__ == "__main__":
    raise SystemExit(main())
