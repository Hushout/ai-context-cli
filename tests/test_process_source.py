"""ProcessSource use case tests (stub adapters)."""

from __future__ import annotations

import pytest

from ai_context.application.process_source import ProcessSourceCommand, ProcessSourceUseCase
from ai_context.domain.exceptions import SummarizerConfigurationError
from ai_context.infrastructure.extractors import StubContentExtractor
from ai_context.infrastructure.fetchers import StubContentFetcher
from ai_context.infrastructure.processors.markdown_converter import html_fragment_to_markdown
from ai_context.infrastructure.summarizers import ExtractiveSummarizer


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


def test_execute_with_summary_requires_summarizer() -> None:
    uc = ProcessSourceUseCase(
        fetcher=StubContentFetcher(),
        extractor=StubContentExtractor(),
        html_to_markdown=html_fragment_to_markdown,
    )
    with pytest.raises(SummarizerConfigurationError):
        uc.execute(ProcessSourceCommand(source="https://example.com/a", include_summary=True))
