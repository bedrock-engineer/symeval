default:
    @just --list

install:
    uv venv --allow-existing
    uv pip install -e .

build:
    uvx marimo -y export session symeval_mo.py
    uvx mobuild export symeval_mo.py src/symeval/__init__.py

test:
    uvx --with marimo --with sympy --with pint pytest symeval_mo.py

# Check if git working tree is clean, bump version, tag, push, create GitHub release.
# Usage: just release 0.2.0
release version: build test
    @git diff --quiet HEAD || { echo "working tree not clean"; exit 1; }
    uv version {{version}}
    git commit -m "Release {{version}}" pyproject.toml
    git tag {{version}}
    git push && git push --tags
    gh release create {{version}} --generate-notes

# Build wheel and publish to PyPI. Run after `just release`.
pypi:
    rm -rf dist/
    uv build
    uv publish
