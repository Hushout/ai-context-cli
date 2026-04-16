"""Markdown structure analyzer (deterministic, no LLM)."""

from __future__ import annotations

import re
from dataclasses import dataclass, field

from ai_context_cli.domain.models import ContentStructure, Section

_HEADING_RE = re.compile(r"^(#{1,3})\s+(.+?)\s*$")
_CLOSING_MARKERS_RE = re.compile(r"\s+#+\s*$")


@dataclass(slots=True)
class _SectionNode:
    heading: str
    level: int
    children: list[_SectionNode] = field(default_factory=list)


def _clean_heading_text(raw_heading: str) -> str:
    """Normalize heading text by trimming spaces and closing markers."""

    without_closing = _CLOSING_MARKERS_RE.sub("", raw_heading)
    return without_closing.strip()


def _iter_markdown_headings(markdown: str) -> list[tuple[int, str]]:
    """Return ATX headings (h1..h3) while ignoring fenced code blocks."""

    headings: list[tuple[int, str]] = []
    in_fence = False
    for line in markdown.splitlines():
        stripped = line.strip()
        if stripped.startswith("```"):
            in_fence = not in_fence
            continue
        if in_fence:
            continue
        match = _HEADING_RE.match(line)
        if match is None:
            continue
        level = len(match.group(1))
        heading = _clean_heading_text(match.group(2))
        if not heading:
            continue
        headings.append((level, heading))
    return headings


def _to_section(node: _SectionNode) -> Section:
    return Section(
        heading=node.heading,
        level=node.level,
        subsections=[_to_section(child) for child in node.children],
    )


def analyze_markdown_structure(markdown: str, fallback_title: str) -> ContentStructure:
    """Build an AI-readable hierarchy from Markdown headings."""

    headings = _iter_markdown_headings(markdown)
    roots: list[_SectionNode] = []
    stack: list[_SectionNode] = []

    for level, heading in headings:
        node = _SectionNode(heading=heading, level=level)
        while stack and stack[-1].level >= node.level:
            stack.pop()
        if stack:
            stack[-1].children.append(node)
        else:
            roots.append(node)
        stack.append(node)

    structure_title = headings[0][1] if headings and headings[0][0] == 1 else fallback_title
    return ContentStructure(
        title=structure_title,
        sections=[_to_section(root) for root in roots],
        entities=[],
    )
