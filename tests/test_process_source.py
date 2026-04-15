"""ProcessSource use case tests (stub adapters)."""

from __future__ import annotations

import logging

import pytest

from ai_context_cli.application.process_source import ProcessSourceCommand, ProcessSourceUseCase
from ai_context_cli.domain.exceptions import SummarizerConfigurationError
from ai_context_cli.domain.models import ExtractedContent, RawContent
from ai_context_cli.domain.ports import ContentExtractor
from ai_context_cli.infrastructure.extractors import StubContentExtractor
from ai_context_cli.infrastructure.fetchers import StubContentFetcher
from ai_context_cli.infrastructure.processors.markdown_converter import html_fragment_to_markdown
from ai_context_cli.infrastructure.summarizers import ExtractiveSummarizer
from ai_context_cli.utils.plain_text import MARKDOWN_TRUNCATION_FOOTER


class _LongArticleExtractor(ContentExtractor):
    """Produces a long article body so Markdown exceeds a small token budget."""

    def extract(self, raw: RawContent) -> ExtractedContent:
        long_p = "word " * 4000
        return ExtractedContent(
            title="Long doc",
            cleaned_html=f"<article><p>{long_p}</p></article>",
        )


def test_execute_without_summary() -> None:
    uc = ProcessSourceUseCase(
        fetcher=StubContentFetcher(),
        extractor=StubContentExtractor(),
        html_to_markdown=html_fragment_to_markdown,
    )
    result = uc.execute(ProcessSourceCommand(source="https://example.com/a", include_summary=False))
    assert result.summary is None
    assert "First stub sentence" in result.markdown


def test_execute_with_stub_summary() -> None:
    uc = ProcessSourceUseCase(
        fetcher=StubContentFetcher(),
        extractor=StubContentExtractor(),
        html_to_markdown=html_fragment_to_markdown,
        summarizer=ExtractiveSummarizer(),
    )
    result = uc.execute(ProcessSourceCommand(source="https://example.com/a", include_summary=True))
    assert result.summary is not None
    assert "Fourth stub sentence" not in result.summary


def test_execute_truncates_markdown_and_logs_when_verbose(caplog: pytest.LogCaptureFixture) -> None:
    uc = ProcessSourceUseCase(
        fetcher=StubContentFetcher(),
        extractor=_LongArticleExtractor(),
        html_to_markdown=html_fragment_to_markdown,
    )
    with caplog.at_level(logging.WARNING):
        result = uc.execute(
            ProcessSourceCommand(
                source="https://example.com/a",
                include_summary=False,
                max_tokens=80,
                verbose=True,
            ),
        )
    assert MARKDOWN_TRUNCATION_FOOTER.strip() in result.markdown
    assert any("truncated" in r.message.lower() for r in caplog.records)


def test_execute_with_summary_requires_summarizer() -> None:
    uc = ProcessSourceUseCase(
        fetcher=StubContentFetcher(),
        extractor=StubContentExtractor(),
        html_to_markdown=html_fragment_to_markdown,
    )
    with pytest.raises(SummarizerConfigurationError):
        uc.execute(ProcessSourceCommand(source="https://example.com/a", include_summary=True))
