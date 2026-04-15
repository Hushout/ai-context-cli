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


MARKDOWN_TRUNCATION_FOOTER = "\n\n[... Contenu tronqué par ai-context-cli ...]\n"


def estimate_tokens_from_text(text: str) -> int:
    """Rough token budget using the same heuristic as :class:`~ai_context_cli.domain.models.ContentMeta`.

    Uses ``max(len(text) // 4, word_count)`` to stay aligned with SPEC (chars / 4).
    """

    words = text.split()
    word_count = len(words)
    return max(len(text) // 4, word_count)


def truncate_markdown_to_token_budget(
    markdown: str,
    max_tokens: int | None,
) -> tuple[str, bool]:
    """Return Markdown possibly truncated so estimated tokens stay within *max_tokens*.

    When truncated, appends :data:`MARKDOWN_TRUNCATION_FOOTER`. If *max_tokens* is ``None``,
    returns the input unchanged.
    """

    if max_tokens is None:
        return markdown, False

    if estimate_tokens_from_text(markdown) <= max_tokens:
        return markdown, False

    footer = MARKDOWN_TRUNCATION_FOOTER
    if estimate_tokens_from_text(footer) > max_tokens:
        return footer[: max(0, min(len(footer), max_tokens * 4))], True

    lo, hi = 0, len(markdown)
    best = 0
    while lo <= hi:
        mid = (lo + hi) // 2
        candidate = markdown[:mid] + footer
        if estimate_tokens_from_text(candidate) <= max_tokens:
            best = mid
            lo = mid + 1
        else:
            hi = mid - 1

    return markdown[:best] + footer, True


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
