"""Typer CLI — thin interface layer over :mod:`ai_context_cli.application`."""

from __future__ import annotations

import logging
import sys
from importlib.metadata import PackageNotFoundError, version
from pathlib import Path
from typing import Annotated, NoReturn

import typer
from rich.console import Console
from rich.logging import RichHandler

from ai_context_cli.application.process_source import ProcessSourceCommand, ProcessSourceUseCase
from ai_context_cli.application.source_gate import normalize_command_source
from ai_context_cli.domain.exceptions import AiContextError
from ai_context_cli.domain.models import (
    OutputConfig,
    OutputFormat,
    ProcessedContent,
    resolve_output_format,
)
from ai_context_cli.domain.ports import ContentFetcher, OutputFormatter, Summarizer
from ai_context_cli.infrastructure.extractors import ReadabilityExtractor
from ai_context_cli.infrastructure.fetchers import FileContentFetcher, HttpContentFetcher
from ai_context_cli.infrastructure.formatters import (
    JsonFormatter,
    MarkdownFormatter,
    PlainFormatter,
)
from ai_context_cli.infrastructure.io import FileWriter
from ai_context_cli.infrastructure.processors import (
    analyze_markdown_structure,
    html_fragment_to_markdown,
)

_err = Console(stderr=True, highlight=False)

_DEFAULT_OPENAI_MODEL = "gpt-4o-mini"


def _version_callback(show_version: bool) -> None:
    if not show_version:
        return
    try:
        resolved_version = version("ai-context-cli")
    except PackageNotFoundError:
        resolved_version = "0.0.0+unknown"
    typer.echo(resolved_version)
    raise typer.Exit()


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


def _build_output_formatter(target_format: OutputFormat) -> OutputFormatter:
    if target_format == "markdown":
        return MarkdownFormatter()
    if target_format == "json":
        return JsonFormatter()
    return PlainFormatter()


def _render_stdout(text: str) -> None:
    """Write final output to stdout without Rich formatting (pipe-friendly)."""

    sys.stdout.write(text)
    sys.stdout.flush()


def main(
    source: Annotated[
        str,
        typer.Argument(help="HTTP(S) URL or path to a local file or directory to convert."),
    ],
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
    structure: Annotated[
        bool,
        typer.Option(
            "--structure/--no-structure",
            help="Attach heading hierarchy and include a TOC in markdown output.",
        ),
    ] = False,
    verbose: Annotated[
        bool,
        typer.Option("--verbose", "-v", help="Log pipeline steps to stderr."),
    ] = False,
    output: Annotated[
        Path | None,
        typer.Option("--output", "-o", help="Write result to a local file path."),
    ] = None,
    output_format: Annotated[
        OutputFormat,
        typer.Option("--format", "-f", help="Output format: markdown, json, or plain."),
    ] = "markdown",
    max_tokens: Annotated[
        int | None,
        typer.Option(
            "--max-tokens",
            min=1,
            help="Truncate Markdown output to roughly this many tokens (approximate).",
        ),
    ] = None,
    show_version: Annotated[
        bool,
        typer.Option(
            "--version",
            callback=_version_callback,
            is_eager=True,
            help="Show ai-context-cli version and exit.",
        ),
    ] = False,
) -> None:
    """Transform a URL or local source through fetch -> Readability -> Markdown."""

    if verbose:
        _configure_verbose_logging()

    try:
        normalized = normalize_command_source(source)
    except AiContextError as exc:
        _handle_domain_error(exc)

    summarizer: Summarizer | None = None
    if summary:
        _maybe_load_dotenv_for_summary()
        resolved_model = model if model is not None else _DEFAULT_OPENAI_MODEL
        summarizer = _build_summarizer_for_cli(resolved_model)

    output_cfg = OutputConfig(
        output_path=str(output) if output is not None else None,
        format=output_format,
    )
    resolved = resolve_output_format(output_cfg.output_path, output_cfg.format)
    if resolved.warning is not None:
        _err.print(f"[yellow]Warning:[/yellow] {resolved.warning}")

    fetcher: ContentFetcher
    if normalized.startswith(("http://", "https://")):
        fetcher = HttpContentFetcher()
    else:
        fetcher = FileContentFetcher()

    use_case = ProcessSourceUseCase(
        fetcher=fetcher,
        extractor=ReadabilityExtractor(),
        html_to_markdown=html_fragment_to_markdown,
        summarizer=summarizer,
        markdown_structure_analyzer=analyze_markdown_structure,
    )
    command = ProcessSourceCommand(
        source=normalized,
        include_summary=summary,
        include_structure=structure,
        max_tokens=max_tokens,
        verbose=verbose,
    )

    try:
        result = use_case.execute(command)
    except AiContextError as exc:
        _handle_domain_error(exc)

    _write_output(result=result, output=output, target_format=resolved.format)


def _write_output(
    result: ProcessedContent,
    output: Path | None,
    target_format: OutputFormat,
) -> None:
    formatter = _build_output_formatter(target_format)
    rendered = formatter.format(result)
    if output is None:
        _render_stdout(rendered)
        return
    writer = FileWriter()
    try:
        writer.write_text(output, rendered)
    except AiContextError as exc:
        _handle_domain_error(exc)


def run_app() -> None:
    """Console entry point (``typer.run`` = single top-level command, no subcommands)."""

    typer.run(main)


def app() -> None:
    """Backward-compatible alias used by some tooling; prefer :func:`run_app`."""

    run_app()
