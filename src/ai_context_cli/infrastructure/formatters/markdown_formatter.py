"""Markdown output formatter."""

from __future__ import annotations

from ai_context_cli.domain.models import ProcessedContent
from ai_context_cli.domain.ports import OutputFormatter


class MarkdownFormatter(OutputFormatter):
    """Serialize pipeline output as Markdown text."""

    def format(self, content: ProcessedContent) -> str:
        rendered = content.markdown.rstrip()
        if content.summary is None:
            return f"{rendered}\n"
        return f"{rendered}\n\n---\n\n## Summary\n\n{content.summary.strip()}\n"
