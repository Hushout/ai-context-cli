"""Plain-text helpers shared by the use case and summarizer adapters."""

from __future__ import annotations

import html
import re

_TAG_RE = re.compile(r"<[^>]+>")
_SPACE_BEFORE_PUNCT_RE = re.compile(r"\s+([.,!?;:])")


def html_to_plain_text_stub(fragment: str) -> str:
    """Remove HTML tags and collapse whitespace (stub quality only)."""

    without_tags = _TAG_RE.sub(" ", fragment)
    collapsed = re.sub(r"\s+", " ", html.unescape(without_tags)).strip()
    return _SPACE_BEFORE_PUNCT_RE.sub(r"\1", collapsed)


def first_three_sentences(text: str) -> str:
    """Return up to the first three sentences of *text* (extractive stub)."""

    cleaned = text.strip()
    if not cleaned:
        return ""

    pieces = re.split(r"(?<=[.!?])\s+", cleaned)
    sentences = [p.strip() for p in pieces if p.strip()]
    if not sentences:
        return cleaned

    return " ".join(sentences[:3])
