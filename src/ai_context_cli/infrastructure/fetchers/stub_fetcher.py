"""Stub :class:`~ai_context_cli.domain.ports.ContentFetcher` (no network)."""

from __future__ import annotations

from ai_context_cli.domain.models import RawContent
from ai_context_cli.domain.ports import ContentFetcher

# Multi-sentence stub body so extractive summary can be exercised (HUX-5).
_STUB_DOCUMENT_HTML = """<!DOCTYPE html>
<html lang="en">
  <body>
    <nav>noise</nav>
    <article>
      <h1>Stub document</h1>
      <p>
        First stub sentence for the pipeline.
        Second stub sentence uses a different terminator!
        Third stub sentence asks a question?
        Fourth stub sentence proves truncation works.
      </p>
    </article>
  </body>
</html>
"""


class StubContentFetcher(ContentFetcher):
    """Returns a fixed HTML document for any HTTP(S) *source* string."""

    def fetch(self, source: str) -> RawContent:
        return RawContent(
            source=source,
            html=_STUB_DOCUMENT_HTML,
            mime_type="text/html",
        )
