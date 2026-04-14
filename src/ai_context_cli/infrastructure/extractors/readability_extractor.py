"""Readability-based :class:`~ai_context_cli.domain.ports.ContentExtractor`."""

from __future__ import annotations

from readability import Document

from ai_context_cli.domain.exceptions import ParseError
from ai_context_cli.domain.models import ExtractedContent, RawContent
from ai_context_cli.domain.ports import ContentExtractor


class ReadabilityExtractor(ContentExtractor):
    """Uses Mozilla Readability (readability-lxml) to isolate the main article HTML."""

    def extract(self, raw: RawContent) -> ExtractedContent:
        if not raw.html or not raw.html.strip():
            raise ParseError("No HTML body available for Readability extraction.")

        doc = Document(raw.html, url=raw.source)
        summary_html = doc.summary()
        title = (doc.title() or "").strip()

        if not summary_html or not summary_html.strip():
            raise ParseError("Readability found no main article content in the HTML.")

        cleaned = summary_html.strip()
        display_title = title if title else "Untitled document"

        return ExtractedContent(title=display_title, cleaned_html=cleaned)
