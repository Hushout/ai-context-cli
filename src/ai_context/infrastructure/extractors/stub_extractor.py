"""Stub :class:`~ai_context.domain.ports.ContentExtractor` (no Readability)."""

from __future__ import annotations

from ai_context.domain.models import ExtractedContent, RawContent
from ai_context.domain.ports import ContentExtractor


class StubContentExtractor(ContentExtractor):
    """Returns a minimal HTML fragment derived from stub *raw* content."""

    def extract(self, raw: RawContent) -> ExtractedContent:
        if raw.html:
            return ExtractedContent(
                title="Stub document",
                cleaned_html=(
                    "<article><p>First stub sentence for the pipeline. "
                    "Second stub sentence uses a different terminator! "
                    "Third stub sentence asks a question? "
                    "Fourth stub sentence proves truncation works.</p>"
                    "</article>"
                ),
            )
        if raw.text is not None:
            return ExtractedContent(
                title="Stub document",
                cleaned_html=f"<article><p>{raw.text}</p></article>",
            )
        return ExtractedContent(title="Stub document", cleaned_html="<article><p></p></article>")
