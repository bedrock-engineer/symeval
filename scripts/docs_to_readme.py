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
tutorial. See ``README.template.md`` for the intended shape.

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
TEMPLATE = REPO_ROOT / "README.template.md"
OUT = REPO_ROOT / "README.generated.md"

DOCS_SITE = "https://bedrock-engineer.github.io/symeval"
GITHUB_SLUG = "bedrock-engineer/symeval"
MOLAB_URL = f"https://molab.marimo.io/github/{GITHUB_SLUG}/blob/main/examples/getting_started.py"
MOLAB_BADGE_IMG = "https://marimo.io/molab-shield.svg"

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
    # Title is single-line ([^\n]+, not .+) so re.DOTALL doesn't let it swallow
    # the whole body into the <summary>.
    text = re.sub(
        r'::: \{\.callout-\w+[^}]*collapse="true"[^}]*\}\n## (?P<title>[^\n]+)\n(?P<body>.*?)\n:::',
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
def _tidy_latex(latex: str) -> str:
    r"""Normalise marimo/sympy LaTeX for GitHub: ``\medspace`` renders poorly, so
    fall back to the standard thin space ``\,`` (as the hand-written README used)."""
    return latex.replace(r"\medspace", r"\,")


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
                out.append(_tidy_latex(html.unescape(match.group(1)).strip()))
    return out


def find_latex(latex: list[str], signature: str) -> str:
    """The first LaTeX output from :func:`session_latex` containing ``signature``."""
    return next((tex for tex in latex if signature in tex), "")


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
    """Drop the ``{python .marimo}`` islands (GitHub cannot execute them) and the
    ``<!---->`` cell separators marimo emits between adjacent markdown cells."""
    body = ISLAND_RE.sub("", body)
    # Blank the marker but keep its newline, so adjacent cells stay separated by a
    # blank line (a table followed immediately by a paragraph breaks on GitHub).
    body = re.sub(r"^<!---->$", "", body, flags=re.MULTILINE)
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
    """The GIF + live-version link that replaces an interactive section's output.

    The molab badge sits on its own centred line beneath the GIF rather than
    inline in the sentence: GitHub strips CSS, so an inline image can't be
    vertically centred with text (``align="middle"`` hangs it below the baseline).
    """
    for key, (path, alt, width) in GIFS.items():
        if key in heading:
            return (
                '<p align="center">\n'
                f'  <img src="{path}" alt="{alt}" width="{width}">\n'
                "  <br>\n"
                f'  <a href="{MOLAB_URL}"><img src="{MOLAB_BADGE_IMG}" alt="Open in molab"></a>\n'
                "</p>\n\n"
                f"Open the [Getting started tutorial]({DOCS_SITE}/getting-started.html) "
                "on the docs website for the live, interactive version."
            )
    return ""


DETAILS_RE = re.compile(
    r"<details>\n<summary>Show code</summary>\n\n```python\n(?P<code>.*?)\n```\n\n</details>",
    re.DOTALL,
)


def inject_ideal_gas_output(section: str, igl_latex: str) -> str:
    """Render the ideal-gas law equation after its (collapsed) code cell.

    That cell ends with a bare ``ideal_gas_law``, whose output is the ``$$PV=RTn$$``
    equation; the code alone carries no output on GitHub, so inject it after the
    ``<details>`` (the SI-unit table below is already plain markdown)."""
    def replace(match: re.Match[str]) -> str:
        if match.group("code").rstrip().endswith("ideal_gas_law"):
            return f"{match.group(0)}\n\n{as_display_math(igl_latex)}"
        return match.group(0)

    return DETAILS_RE.sub(replace, section, count=1)


def build_advanced_body() -> str:
    """Transform getting-started.qmd into the README's "More advanced" body."""
    _, body = split_frontmatter(GETTING_STARTED.read_text())
    body = re.sub(r"^\[!\[Open in molab\].*$\n?", "", body, flags=re.MULTILINE)  # drop top badge
    body = strip_islands(body)
    body = qmd_to_gfm(body)

    # Split on "## " section headings; drop the intro before the first one.
    parts = re.split(r"(?m)^(## .+)$", body)
    latex = session_latex()
    igl_latex = find_latex(latex, "R T n")  # the "P V = R T n" equation output

    out: list[str] = []
    for i in range(1, len(parts), 2):
        heading, content = parts[i].strip(), parts[i + 1].strip("\n")
        if "Axial stress under a compressive force" in heading:
            content = inject_axial_outputs(content, latex)
            out.append(f"{heading}\n\n{content}")
        elif "Ideal Gas Law" in heading:
            content = inject_ideal_gas_output(content, igl_latex)
            out.append(f"{heading}\n\n{content}\n\n{gif_block(heading)}")
        elif any(key in heading for key in GIFS):
            out.append(f"{heading}\n\n{content}\n\n{gif_block(heading)}")
        else:
            out.append(f"{heading}\n\n{content}")
    return "\n\n".join(out).strip() + "\n"


# --------------------------------------------------------------------------- #
def main() -> None:
    top, inspiration = build_top_and_inspiration()
    advanced = build_advanced_body()

    readme = TEMPLATE.read_text()
    for marker, value in {
        "<!-- {{TOP}} -->": top.rstrip(),
        "<!-- {{BODY}} -->": advanced.rstrip(),
        "<!-- {{INSPIRATION}} -->": inspiration.rstrip(),
    }.items():
        if marker not in readme:
            raise SystemExit(f"template {TEMPLATE.name} is missing marker {marker}")
        readme = readme.replace(marker, value)

    OUT.write_text(readme)
    print(f"Wrote {OUT.relative_to(REPO_ROOT)} ({len(readme.splitlines())} lines)")


if __name__ == "__main__":
    main()
