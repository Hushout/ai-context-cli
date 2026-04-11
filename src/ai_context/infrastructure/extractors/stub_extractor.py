"""Stub :class:`~ai_context.domain.ports.ContentExtractor` (no Readability)."""

from __future__ import annotations

from ai_context.domain.models import RawContent
from ai_context.domain.ports import ContentExtractor


class StubContentExtractor(ContentExtractor):
    """Returns a minimal HTML fragment derived from stub *raw* content."""

    def extract(self, raw: RawContent) -> str:
        if raw.html:
            return (
                "<article><h1>Stub document</h1>"
                "<p>First stub sentence for the pipeline. "
                "Second stub sentence uses a different terminator! "
                "Third stub sentence asks a question? "
                "Fourth stub sentence proves truncation works.</p>"
                "</article>"
            )
        if raw.text is not None:
            return f"<article><p>{raw.text}</p></article>"
        return "<article><p></p></article>"
