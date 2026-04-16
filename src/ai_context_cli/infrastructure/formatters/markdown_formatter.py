"""Markdown output formatter."""

from __future__ import annotations

import re
import unicodedata

from ai_context_cli.domain.models import ProcessedContent, Section
from ai_context_cli.domain.ports import OutputFormatter


def _slugify_heading(heading: str) -> str:
    normalized = unicodedata.normalize("NFKD", heading)
    ascii_text = normalized.encode("ascii", "ignore").decode("ascii").lower()
    sanitized = re.sub(r"[^a-z0-9\s-]", "", ascii_text)
    collapsed = re.sub(r"[\s-]+", "-", sanitized).strip("-")
    return collapsed or "section"


def _walk_sections(sections: list[Section]) -> list[tuple[int, str]]:
    flattened: list[tuple[int, str]] = []
    for section in sections:
        if section.level <= 3:
            flattened.append((section.level, section.heading))
        flattened.extend(_walk_sections(section.subsections))
    return flattened


def _render_toc(markdown: str, content: ProcessedContent) -> str:
    if content.structure is None or not content.structure.sections:
        return markdown

    flattened = _walk_sections(content.structure.sections)
    if not flattened:
        return markdown

    toc_lines = ["## Table of Contents", ""]
    for level, heading in flattened:
        depth = max(level - 1, 0)
        indent = "  " * depth
        toc_lines.append(f"{indent}- [{heading}](#{_slugify_heading(heading)})")
    toc_block = "\n".join(toc_lines)

    if markdown.startswith("# "):
        first_break = markdown.find("\n")
        if first_break != -1:
            title_line = markdown[:first_break]
            remainder = markdown[first_break + 1 :].lstrip("\n")
            if remainder:
                return f"{title_line}\n\n{toc_block}\n\n{remainder}"
            return f"{title_line}\n\n{toc_block}"
    return f"{toc_block}\n\n{markdown}"


class MarkdownFormatter(OutputFormatter):
    """Serialize pipeline output as Markdown text."""

    def format(self, content: ProcessedContent) -> str:
        rendered = _render_toc(content.markdown.rstrip(), content)
        if content.summary is None:
            return f"{rendered}\n"
        return f"{rendered}\n\n---\n\n## Summary\n\n{content.summary.strip()}\n"
