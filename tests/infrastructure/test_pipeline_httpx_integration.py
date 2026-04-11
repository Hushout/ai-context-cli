"""End-to-end pipeline tests with ``pytest-httpx`` (no real network)."""

from __future__ import annotations

from pytest_httpx import HTTPXMock

from ai_context.application.process_source import ProcessSourceCommand, ProcessSourceUseCase
from ai_context.infrastructure.extractors import ReadabilityExtractor
from ai_context.infrastructure.fetchers import HttpContentFetcher
from ai_context.infrastructure.processors.markdown_converter import html_fragment_to_markdown

_BLOG_HTML = """<!DOCTYPE html>
<html><head><title>My Article</title></head>
<body>
  <article><h1>My Article</h1><p>Alpha sentence. Beta sentence.</p></article>
</body></html>
"""


def test_full_pipeline_mocked_http(httpx_mock: HTTPXMock) -> None:
    httpx_mock.add_response(url="https://blog.test/post", text=_BLOG_HTML)
    uc = ProcessSourceUseCase(
        fetcher=HttpContentFetcher(),
        extractor=ReadabilityExtractor(),
        html_to_markdown=html_fragment_to_markdown,
    )
    cmd = ProcessSourceCommand(source="https://blog.test/post", include_summary=False)
    result = uc.execute(cmd)
    assert "Alpha sentence" in result.markdown
    assert result.title == "My Article"
