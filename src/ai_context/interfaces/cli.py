"""Typer CLI — thin interface layer over :mod:`ai_context.application`."""

from __future__ import annotations

import logging
import sys
from typing import Annotated, NoReturn

import typer
from rich.console import Console
from rich.logging import RichHandler

from ai_context.application.process_source import ProcessSourceCommand, ProcessSourceUseCase
from ai_context.application.source_gate import validate_http_url_command_source
from ai_context.domain.exceptions import AiContextError
from ai_context.infrastructure.extractors import StubContentExtractor
from ai_context.infrastructure.fetchers import StubContentFetcher

_err = Console(stderr=True, highlight=False)


def _configure_verbose_logging() -> None:
    """Route *ai_context* logs through Rich on stderr."""

    pkg = logging.getLogger("ai_context")
    pkg.setLevel(logging.INFO)
    handler = RichHandler(
        console=_err,
        show_time=True,
        show_path=False,
        rich_tracebacks=True,
    )
    handler.setLevel(logging.INFO)
    pkg.handlers.clear()
    pkg.addHandler(handler)
    pkg.propagate = False


def _handle_domain_error(exc: AiContextError) -> NoReturn:
    _err.print(f"[bold red]Error:[/bold red] {exc}")
    raise typer.Exit(code=exc.exit_code)


def _render_stdout(markdown: str, summary: str | None) -> None:
    """Write result to stdout without Rich formatting (pipe-friendly)."""

    sys.stdout.write(markdown)
    if summary is not None:
        sys.stdout.write("\n\n---\n\n## Summary (stub)\n\n")
        sys.stdout.write(summary)
        sys.stdout.write("\n")
    sys.stdout.flush()


def main(
    source: Annotated[str, typer.Argument(help="HTTP(S) URL to process (stub pipeline).")],
    summary: Annotated[
        bool,
        typer.Option(
            "--summary/--no-summary",
            help="Attach a minimal extractive summary (first three stub sentences).",
        ),
    ] = False,
    verbose: Annotated[
        bool,
        typer.Option("--verbose", "-v", help="Log pipeline steps to stderr."),
    ] = False,
) -> None:
    """Transform a URL through the stub fetch/extract pipeline (foundation / HUX-5)."""

    if verbose:
        _configure_verbose_logging()

    try:
        normalized = validate_http_url_command_source(source)
    except AiContextError as exc:
        _handle_domain_error(exc)

    use_case = ProcessSourceUseCase(
        fetcher=StubContentFetcher(),
        extractor=StubContentExtractor(),
    )
    command = ProcessSourceCommand(source=normalized, include_summary=summary)

    try:
        result = use_case.execute(command)
    except AiContextError as exc:
        _handle_domain_error(exc)

    _render_stdout(result.markdown, result.summary)


def run_app() -> None:
    """Console entry point (``typer.run`` = single top-level command, no subcommands)."""

    typer.run(main)


def app() -> None:
    """Backward-compatible alias used by some tooling; prefer :func:`run_app`."""

    run_app()
