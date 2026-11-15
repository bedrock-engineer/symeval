"""Subprocess entry point for the Quarto marimo engine."""

from __future__ import annotations

import asyncio
import json
import os
import sys
from collections.abc import Callable
from contextlib import redirect_stdout
from pathlib import Path
from typing import Any, ClassVar, cast
from xml.etree.ElementTree import Element

from marimo._convert.markdown.to_ir import (
    MarimoMdParser,
    SafeWrap as SafeWrapGeneric,
)

from quarto_marimo.authoring import document_options, normalize_markdown
from quarto_marimo.compiler import compile_page
from quarto_marimo.document import collect_page
from quarto_marimo.protocol import CompiledMarimoPage, JsonObject
from quarto_marimo.static import render_static_page

ConversionResult = dict[str, Any]
SafeWrap = SafeWrapGeneric[ConversionResult]
ExportCallback = Callable[[Element], SafeWrap]


def convert_markdown(
    text: str,
    *,
    filename: str,
    interactive: bool,
    global_eval: bool = True,
    foldable: bool = False,
) -> dict[str, Any]:
    """Compile one document.

    `foldable` says whether static output lands in a format that can still
    collapse code, which is HTML rendered without the browser runtime.
    """
    page_options = document_options(text)
    callback = (
        interactive_export(
            filename=filename,
            global_eval=global_eval,
            page_options=page_options,
        )
        if interactive
        else static_export(
            filename=filename,
            global_eval=global_eval,
            page_options=page_options,
            foldable=foldable,
        )
    )

    class QuartoMarimoParser(MarimoMdParser):
        output_formats: ClassVar[dict[str, ExportCallback]] = {  # type: ignore[assignment, misc]
            "quarto-marimo": callback,
        }

    parser = QuartoMarimoParser(output_format="quarto-marimo")  # type: ignore[arg-type]
    return cast(ConversionResult, parser.convert(normalize_markdown(text)))


def interactive_export(
    *,
    filename: str,
    global_eval: bool,
    page_options: JsonObject,
) -> ExportCallback:
    def export(root: Element) -> SafeWrap:
        request = collect_page(
            root,
            filename=filename,
            global_eval=global_eval,
            page_options=page_options,
        )
        page = asyncio.run(
            compile_page(
                request.to_json(),
                development_url=os.environ.get("QUARTO_MARIMO_DEBUG_ENDPOINT"),
                version_override=os.environ.get("QUARTO_MARIMO_VERSION"),
            )
        )
        return SafeWrap(
            {
                "kind": "page",
                "page": page,
            }
        )

    return export


def static_export(
    *,
    filename: str,
    global_eval: bool,
    page_options: JsonObject,
    foldable: bool,
) -> ExportCallback:
    def export(root: Element) -> SafeWrap:
        request = collect_page(
            root,
            filename=filename,
            global_eval=global_eval,
            page_options=page_options,
            foldable=foldable,
        )
        page = CompiledMarimoPage.from_json(
            asyncio.run(compile_page(request.to_json()))
        )
        return SafeWrap(
            {
                "kind": "static",
                "outputs": render_static_page(request, page),
            }
        )

    return export


def main(argv: list[str] | None = None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    if len(args) not in (2, 3):
        raise ValueError("expected reference file, output mode, and optional eval mode")
    reference_file, output_mode = args[:2]
    global_eval = args[2].lower() == "yes" if len(args) == 3 else True
    # `html` is an interactive page; `html-static` is an HTML format rendered
    # without the browser runtime; `static` is every other format.
    interactive = output_mode.lower() == "html"
    # Only HTML can fold code, whether or not the page keeps its runtime.
    foldable = output_mode.lower() in ("html", "html-static")
    os.environ["MARIMO_NO_JS"] = str(not interactive).lower()

    # The engine always sends UTF-8 bytes. Bypass the locale-dependent text
    # wrappers so a cp932 or similar host locale cannot corrupt the document.
    source = sys.stdin.buffer.read().decode("utf-8")
    if not source:
        source = Path(reference_file).read_text(encoding="utf-8")
    with redirect_stdout(sys.stderr):
        result = convert_markdown(
            source,
            filename=reference_file,
            interactive=interactive,
            global_eval=global_eval,
            foldable=foldable,
        )
    sys.stdout.buffer.write(json.dumps(result).encode("utf-8"))
    sys.stdout.flush()
    return 0
