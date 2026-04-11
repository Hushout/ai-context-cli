"""ProcessSource use case — orchestrates fetch → extract → stub output."""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass
from datetime import UTC, datetime

from ai_context.application.extractive_stub import first_three_sentences, html_to_plain_text_stub
from ai_context.domain.models import ContentMeta, ProcessedContent
from ai_context.domain.ports import ContentExtractor, ContentFetcher

logger = logging.getLogger(__name__)


@dataclass(frozen=True, slots=True)
class ProcessSourceCommand:
    """Input DTO for :class:`ProcessSourceUseCase`."""

    source: str
    include_summary: bool = False


class ProcessSourceUseCase:
    """Coordinates the processing pipeline using injected ports."""

    def __init__(self, fetcher: ContentFetcher, extractor: ContentExtractor) -> None:
        self._fetcher = fetcher
        self._extractor = extractor

    def execute(self, cmd: ProcessSourceCommand) -> ProcessedContent:
        started = time.perf_counter()
        logger.info("Fetching source: %s", cmd.source)
        raw = self._fetcher.fetch(cmd.source)

        logger.info("Extracting readable content (stub)")
        extracted_html = self._extractor.extract(raw)
        plain = html_to_plain_text_stub(extracted_html)

        title = "Stub document"
        markdown_lines = [f"# {title}", "", plain]
        markdown = "\n".join(markdown_lines)

        summary: str | None = None
        if cmd.include_summary:
            summary = first_three_sentences(plain)
            logger.info("Stub extractive summary enabled (first three sentences)")

        words = plain.split()
        word_count = len(words)
        estimated_tokens = max(len(plain) // 4, word_count)

        elapsed_ms = int((time.perf_counter() - started) * 1000)
        meta = ContentMeta(
            word_count=word_count,
            estimated_tokens=estimated_tokens,
            extracted_at=datetime.now(tz=UTC),
            processing_ms=elapsed_ms,
        )

        logger.info("Pipeline finished in %s ms", meta.processing_ms)
        return ProcessedContent(
            source=cmd.source,
            title=title,
            markdown=markdown,
            summary=summary,
            structure=None,
            meta=meta,
        )
