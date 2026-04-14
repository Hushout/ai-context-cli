"""Tests for ``ReadabilityExtractor``."""

from __future__ import annotations

import pytest

from ai_context_cli.domain.exceptions import ParseError
from ai_context_cli.domain.models import RawContent
from ai_context_cli.infrastructure.extractors.readability_extractor import ReadabilityExtractor

_ARTICLE_HTML = """<!DOCTYPE html>
<html lang="en">
  <head><title>Page title from head</title></head>
  <body>
    <header><nav>Home · About · Noise</nav></header>
    <article>
      <h1>Visible headline</h1>
      <p>First paragraph keeps the substance.</p>
      <p>Second paragraph for length.</p>
    </article>
    <aside>Advertisement buy now</aside>
  </body>
</html>
"""


def test_readability_returns_title_and_cleaned_html() -> None:
    raw = RawContent(
        source="https://example.com/story",
        html=_ARTICLE_HTML,
        mime_type="text/html",
    )
    extracted = ReadabilityExtractor().extract(raw)
    assert "First paragraph" in extracted.cleaned_html
    assert "Home · About" not in extracted.cleaned_html
    assert extracted.title


def test_readability_raises_parse_error_when_no_html() -> None:
    raw = RawContent(
        source="https://example.com/empty",
        html="   ",
        mime_type="text/html",
    )
    with pytest.raises(ParseError):
        ReadabilityExtractor().extract(raw)
