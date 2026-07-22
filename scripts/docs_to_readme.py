# /// script
# requires-python = ">=3.12"
# dependencies = []
# ///
"""Generate ``README.generated.md`` from the docs sources.

The README is assembled from the same content that drives the docs website, so
the two stay in sync:

    docs/index.qmd            -> the top (intro, highlights, quickstart) + Inspiration
    docs/getting-started.qmd  -> the "More advanced" body (prose + code)
    examples/__marimo__/session/getting_started.py.json
                              -> the computed marimo outputs (LaTeX), which the
                                 .qmd export omits

The three interactive examples (DataFrame table, HSS member, ideal-gas piston)
replace their live marimo widget with a recorded GIF plus a link to the live
tutorial. See ``README-template.md`` for the intended shape.

This is the first-pass generator: it writes ``README.generated.md`` (never
``README.md``) so the output can be diffed against the hand-written README
before adopting it. It is intentionally not wired into any task yet.

Run it with uv::

    uv run scripts/docs_to_readme.py
"""

from __future__ import annotations

import html
import json
import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
INDEX = REPO_ROOT / "docs" / "index.qmd"
GETTING_STARTED = REPO_ROOT / "docs" / "getting-started.qmd"
SESSION = REPO_ROOT / "examples" / "__marimo__" / "session" / "getting_started.py.json"
OUT = REPO_ROOT / "README.generated.md"

DOCS_SITE = "https://bedrock-engineer.github.io/symeval"
GITHUB_SLUG = "bedrock-engineer/symeval"
MOLAB_URL = f"https://molab.marimo.io/https://github.com/{GITHUB_SLUG}/blob/main/examples/getting_started.py"
MOLAB_BADGE = f"[![Open in molab](https://img.shields.io/badge/Open%20in-molab-63805e)]({MOLAB_URL})"

# The GIF that replaces each interactive section's marimo output, keyed by a
# substring of the section heading.
GIFS = {
    "quantity_evalf": (
        "docs/public/table.gif",
        "Selecting a member row in the table updates its axial-stress symbolic evaluation below.",
        760,
    ),
    "Axial Resistance": (
        "docs/public/hss.gif",
        "Increasing the beam length recomputes the Euler buckling stress, lambda factor, "
        "axial resistance, and demand-capacity ratio, with DCR rising past 1.0.",
        620,
    ),
    "Ideal Gas Law": (
        "docs/public/piston.gif",
        "Changing the solve-for radio button and the sliders updates the piston and the "
        "symbolic evaluation of the ideal gas law in real time.",
        620,
    ),
}

# The static tail has no source in the docs; the Inspiration section is spliced
# in between Feedback and Authors (see README-template.md for the order).
FEEDBACK_MD = """\
"""

FEEDBACK_AUTHORS_LICENSE_MD = """\
## Feedback & contributing

Found a bug or have a feature request? [Open an issue](https://github.com/bedrock-engineer/symeval/issues), pull requests are welcome too.

Want to add a worked example? See [`CONTRIBUTING.md`](CONTRIBUTING.md) for the dev setup, the docs dev server, and how to add a notebook.

The package is a single marimo notebook (`symeval_mo.py`) with `## EXPORT`-marked cells extracted into `src/symeval/` via [mobuild](https://github.com/koaning/mobuild); see [`CLAUDE.md`](CLAUDE.md) for the project layout and [`RELEASING.md`](RELEASING.md) for the release workflow.

## Authors

Built and maintained by the [Bedrock.engineer](https://bedrock.engineer)s ([Joost Gevaert](https://github.com/JoostGevaert) and [Jules Blom](https://github.com/JulesBlm)).

## License

Apache License 2.0, see [LICENSE](LICENSE).
"""


# --------------------------------------------------------------------------- #
# Shared Quarto -> GitHub-Markdown conversions
# --------------------------------------------------------------------------- #
def qmd_to_gfm(text: str) -> str:
    """Convert the Quarto-isms both pages share into GitHub-flavoured Markdown."""
    # Relative .qmd links -> docs-site URLs.
    text = re.sub(
        r"\]\((?!https?:)([\w-]+)\.qmd(#[\w-]+)?\)",
        lambda m: f"]({DOCS_SITE}/{m.group(1)}.html{m.group(2) or ''})",
        text,
    )
    # Pandoc attribute spans on links, e.g. [Get started](url){.btn .btn-primary}.
    text = re.sub(r"\)\{\.[^}]*\}", ")", text)
    # Collapsible callout: ::: {.callout-note collapse="true"} ## Title ... :::
    text = re.sub(
        r'::: \{\.callout-\w+[^}]*collapse="true"[^}]*\}\n## (?P<title>.+)\n(?P<body>.*?)\n:::',
        lambda m: (
            "<details>\n"
            f"<summary><strong>{m.group('title')}</strong></summary>\n\n"
            f"{_clean_callout_body(m.group('body'))}\n\n"
            "</details>"
        ),
        text,
        flags=re.DOTALL,
    )
    # Simple (non-collapsible) callout -> blockquote.
    text = re.sub(
        r"::: \{\.callout-\w+[^}]*\}\n(?P<body>.*?)\n:::",
        lambda m: "\n".join(f"> {line}" if line else ">" for line in m.group("body").splitlines()),
        text,
        flags=re.DOTALL,
    )
    return text


def _clean_callout_body(body: str) -> str:
    """Tidy a callout body: drop the Pandoc rule of dashes, trim edges."""
    body = re.sub(r"^-{3,}$", "---", body.strip(), flags=re.MULTILINE)
    return body.strip()


# --------------------------------------------------------------------------- #
# Session outputs
# --------------------------------------------------------------------------- #
def session_latex() -> list[str]:
    """Ordered LaTeX outputs (arithmatex ``marimo-tex`` blocks) from the session.

    For getting_started these are, in order: the axial-stress equation, the
    default / verbose / one-line evaluations, then the selected-member
    evaluation in the DataFrame section (which the GIF replaces).
    """
    data = json.loads(SESSION.read_text())
    out: list[str] = []
    for cell in data["cells"]:
        for output in cell.get("outputs", []):
            if output.get("type") != "data":
                continue
            markup = output["data"].get("text/html", "")
            match = re.search(r"<marimo-tex[^>]*>\s*\|\|\[(.*?)\|\|\]\s*</marimo-tex>", markup, re.DOTALL)
            if match:
                out.append(html.unescape(match.group(1)).strip())
    return out


def as_display_math(latex: str) -> str:
    """Wrap an extracted LaTeX string as a ``$$ … $$`` display-math block."""
    return f"$$\n{latex}\n$$"


# --------------------------------------------------------------------------- #
# index.qmd -> README top + Inspiration
# --------------------------------------------------------------------------- #
def split_frontmatter(text: str) -> tuple[dict[str, str], str]:
    """Return a shallow ``{key: value}`` of the YAML frontmatter and the body."""
    if not text.startswith("---\n"):
        return {}, text
    end = text.index("\n---\n", 4)
    front = {}
    for line in text[4:end].splitlines():
        m = re.match(r"(\w+):\s*(.*)", line)
        if m:
            front[m.group(1)] = m.group(2).strip().strip('"')
    return front, text[end + 5 :]


def build_top_and_inspiration() -> tuple[str, str]:
    """The README heading + intro/highlights/quickstart, and the Inspiration block."""
    front, body = split_frontmatter(INDEX.read_text())

    # Everything before "Head to the [Getting started]" is the top of the README.
    cut = body.index("Head to the [Getting started]")
    top_body = body[:cut].rstrip()

    # The Inspiration section (near the end) is reused verbatim.
    insp = re.search(r"^## Inspiration\n.*", body, re.DOTALL | re.MULTILINE)
    inspiration = qmd_to_gfm(insp.group(0).strip()) if insp else ""

    title = front.get("title", "SymEval")
    subtitle = front.get("subtitle", "")
    top = f"# {title}\n\n"
    if subtitle:
        top += f"**{subtitle}**\n\n"
    top += qmd_to_gfm(top_body).strip() + "\n"
    return top, inspiration


# --------------------------------------------------------------------------- #
# getting-started.qmd -> the "More advanced" body
# --------------------------------------------------------------------------- #
ISLAND_RE = re.compile(r"^```\{python \.marimo\}\n.*?\n```[ \t]*$\n?", re.DOTALL | re.MULTILINE)
CODE_BLOCK_RE = re.compile(r"```python\n(?P<code>.*?)\n```", re.DOTALL)


def strip_islands(body: str) -> str:
    """Drop the ``{python .marimo}`` islands (GitHub cannot execute them)."""
    body = ISLAND_RE.sub("", body)
    return re.sub(r"\n{3,}", "\n\n", body)


def inject_axial_outputs(section: str, latex: list[str]) -> str:
    """Insert the LaTeX outputs after their code blocks in the axial-stress section.

    Matched by code signature so the mapping survives cell reordering: the bare
    equation, the default evaluation, then the ``verbose`` and ``one_line`` modes.
    The imports and the ``fa_inputs`` dict echo get no output.
    """
    eq, default, verbose, one_line = latex[0], latex[1], latex[2], latex[3]

    def replace(match: re.Match[str]) -> str:
        code = match.group("code")
        block = match.group(0)
        if "Equality(Symbol(r" in code and code.rstrip().endswith("axial_stress_eq"):
            return f"{block}\n\n{as_display_math(eq)}"
        if 'mode="verbose"' in code:
            return f"{block}\n\n{as_display_math(verbose)}"
        if 'mode="one_line"' in code:
            return f"{block}\n\n{as_display_math(one_line)}"
        if "sym_evalf(" in code and "mode=" not in code and code.strip().startswith("axial_stress ="):
            return f"{block}\n\n{as_display_math(default)}"
        return block

    return CODE_BLOCK_RE.sub(replace, section)


def gif_block(heading: str) -> str:
    """The GIF + live-version link that replaces an interactive section's output."""
    for key, (path, alt, width) in GIFS.items():
        if key in heading:
            return (
                '<p align="center">\n'
                f'  <img src="{path}" alt="{alt}" width="{width}">\n'
                "</p>\n\n"
                f"Open the [Getting started tutorial]({DOCS_SITE}/getting-started.html) "
                f"on the docs website, or {MOLAB_BADGE} for the live, interactive version."
            )
    return ""


def collapse_js_blocks(section: str) -> str:
    """Fold a bare ```js piston block into a <details> so it doesn't dominate."""
    return re.sub(
        r"```js\n(.*?)\n```",
        lambda m: (
            "<details>\n<summary>Show the piston JavaScript</summary>\n\n"
            f"```js\n{m.group(1)}\n```\n\n</details>"
        ),
        section,
        flags=re.DOTALL,
    )


def build_advanced_body() -> str:
    """Transform getting-started.qmd into the README's "More advanced" body."""
    _, body = split_frontmatter(GETTING_STARTED.read_text())
    body = re.sub(r"^\[!\[Open in molab\].*$\n?", "", body, flags=re.MULTILINE)  # drop top badge
    body = strip_islands(body)
    body = qmd_to_gfm(body)

    # Split on "## " section headings; drop the intro before the first one.
    parts = re.split(r"(?m)^(## .+)$", body)
    latex = session_latex()

    out: list[str] = []
    for i in range(1, len(parts), 2):
        heading, content = parts[i].strip(), parts[i + 1].strip("\n")
        if "Axial stress under a compressive force" in heading:
            content = inject_axial_outputs(content, latex)
            out.append(f"{heading}\n\n{content}")
        elif any(key in heading for key in GIFS):
            content = collapse_js_blocks(content)
            out.append(f"{heading}\n\n{content}\n\n{gif_block(heading)}")
        else:
            out.append(f"{heading}\n\n{content}")
    return "\n\n".join(out).strip() + "\n"


# --------------------------------------------------------------------------- #
def main() -> None:
    top, inspiration = build_top_and_inspiration()
    advanced = build_advanced_body()

    readme = (
        top
        + "\n# More advanced SymEval functionality\n\n"
        + advanced
        + "\n"
        + FEEDBACK_MD
        + "\n"
        + inspiration
        + "\n\n"
        + FEEDBACK_AUTHORS_LICENSE_MD
    )
    OUT.write_text(readme)
    print(f"Wrote {OUT.relative_to(REPO_ROOT)} ({len(readme.splitlines())} lines)")


if __name__ == "__main__":
    main()
