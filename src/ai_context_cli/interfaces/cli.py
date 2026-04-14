"""Typer CLI — thin interface layer over :mod:`ai_context_cli.application`."""

from __future__ import annotations

import logging
import sys
from typing import Annotated, NoReturn

import typer
from rich.console import Console
from rich.logging import RichHandler

from ai_context_cli.application.process_source import ProcessSourceCommand, ProcessSourceUseCase
from ai_context_cli.application.source_gate import validate_http_url_command_source
from ai_context_cli.domain.exceptions import AiContextError
from ai_context_cli.domain.ports import Summarizer
from ai_context_cli.infrastructure.extractors import ReadabilityExtractor
from ai_context_cli.infrastructure.fetchers import HttpContentFetcher
from ai_context_cli.infrastructure.processors.markdown_converter import html_fragment_to_markdown

_err = Console(stderr=True, highlight=False)

_DEFAULT_OPENAI_MODEL = "gpt-4o-mini"


def _configure_verbose_logging() -> None:
    """Route *ai_context_cli* logs through Rich on stderr."""

    pkg = logging.getLogger("ai_context_cli")
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


def _maybe_load_dotenv_for_summary() -> None:
    """Load ``.env`` from the current working directory when summarization may need keys."""

    from dotenv import load_dotenv  # noqa: PLC0415 — keep CLI import graph light

    load_dotenv()


def _build_summarizer_for_cli(model: str) -> Summarizer:
    """Factory hook — tests patch this symbol to avoid real LLM calls."""

    from ai_context_cli.infrastructure.summarizers.litellm_summarizer import (  # noqa: PLC0415
        LiteLLMSummarizer,
    )

    return LiteLLMSummarizer(model=model, timeout_seconds=30.0)


def _render_stdout(markdown: str, summary: str | None) -> None:
    """Write result to stdout without Rich formatting (pipe-friendly)."""

    sys.stdout.write(markdown)
    if summary is not None:
        sys.stdout.write("\n\n---\n\n## Summary\n\n")
        sys.stdout.write(summary)
        sys.stdout.write("\n")
    sys.stdout.flush()


def main(
    source: Annotated[str, typer.Argument(help="HTTP(S) URL to fetch and convert to Markdown.")],
    summary: Annotated[
        bool,
        typer.Option(
            "--summary/--no-summary",
            help="Attach an LLM summary (LiteLLM; default model OpenAI gpt-4o-mini).",
        ),
    ] = False,
    model: Annotated[
        str | None,
        typer.Option(
            "--model",
            help=(
                "LiteLLM model id (e.g. gpt-4o-mini, anthropic/claude-3-5-sonnet-latest, "
                "ollama/llama3). OpenAI-style bare ids use OPENAI_API_KEY."
            ),
        ),
    ] = None,
    verbose: Annotated[
        bool,
        typer.Option("--verbose", "-v", help="Log pipeline steps to stderr."),
    ] = False,
) -> None:
    """Transform an HTTP(S) URL through fetch -> Readability -> Markdown."""

    if verbose:
        _configure_verbose_logging()

    try:
        normalized = validate_http_url_command_source(source)
    except AiContextError as exc:
        _handle_domain_error(exc)

    summarizer: Summarizer | None = None
    if summary:
        _maybe_load_dotenv_for_summary()
        resolved_model = model if model is not None else _DEFAULT_OPENAI_MODEL
        summarizer = _build_summarizer_for_cli(resolved_model)

    use_case = ProcessSourceUseCase(
        fetcher=HttpContentFetcher(),
        extractor=ReadabilityExtractor(),
        html_to_markdown=html_fragment_to_markdown,
        summarizer=summarizer,
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
