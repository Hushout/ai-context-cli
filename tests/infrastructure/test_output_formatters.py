"""Tests for output formatters."""

from __future__ import annotations

import json
from datetime import UTC, datetime

from ai_context_cli.domain.models import ContentMeta, ProcessedContent
from ai_context_cli.infrastructure.formatters import JsonFormatter, MarkdownFormatter, PlainFormatter


def _processed_content() -> ProcessedContent:
    return ProcessedContent(
        source="https://example.com/post",
        title="Example title",
        markdown="# Example title\n\nHello **world** and `code`.",
        summary="Brief summary.",
        structure=None,
        meta=ContentMeta(
            word_count=4,
            estimated_tokens=8,
            extracted_at=datetime(2026, 4, 15, 0, 0, tzinfo=UTC),
            processing_ms=12,
        ),
    )


def test_markdown_formatter_includes_summary_block() -> None:
    rendered = MarkdownFormatter().format(_processed_content())
    assert rendered.startswith("# Example title")
    assert "## Summary" in rendered


def test_json_formatter_outputs_processed_content_shape() -> None:
    rendered = JsonFormatter().format(_processed_content())
    payload = json.loads(rendered)
    assert payload["source"] == "https://example.com/post"
    assert "markdown" in payload
    assert "meta" in payload
    assert payload["meta"]["processing_ms"] == 12


def test_plain_formatter_strips_markdown_syntax() -> None:
    rendered = PlainFormatter().format(_processed_content())
    assert "# Example title" not in rendered
    assert "**world**" not in rendered
    assert "world" in rendered
    assert "Summary" in rendered
