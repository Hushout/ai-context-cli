"""ProcessSource use case tests (stub adapters)."""

from __future__ import annotations

from ai_context.application.process_source import ProcessSourceCommand, ProcessSourceUseCase
from ai_context.infrastructure.extractors import StubContentExtractor
from ai_context.infrastructure.fetchers import StubContentFetcher


def test_execute_without_summary() -> None:
    uc = ProcessSourceUseCase(fetcher=StubContentFetcher(), extractor=StubContentExtractor())
    result = uc.execute(ProcessSourceCommand(source="https://example.com/a", include_summary=False))
    assert result.summary is None
    assert "First stub sentence" in result.markdown


def test_execute_with_stub_summary() -> None:
    uc = ProcessSourceUseCase(fetcher=StubContentFetcher(), extractor=StubContentExtractor())
    result = uc.execute(ProcessSourceCommand(source="https://example.com/a", include_summary=True))
    assert result.summary is not None
    assert "Fourth stub sentence" not in result.summary
