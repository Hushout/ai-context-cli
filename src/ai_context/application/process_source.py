"""ProcessSource use case — orchestrates fetch → extract → Markdown output."""

from __future__ import annotations

import logging
import time
from collections.abc import Callable
from dataclasses import dataclass
from datetime import UTC, datetime

from ai_context.domain.exceptions import SummarizerConfigurationError
from ai_context.domain.models import ContentMeta, ProcessedContent
from ai_context.domain.ports import ContentExtractor, ContentFetcher, Summarizer
from ai_context.utils.plain_text import html_to_plain_text_stub

logger = logging.getLogger(__name__)


@dataclass(frozen=True, slots=True)
class ProcessSourceCommand:
    """Input DTO for :class:`ProcessSourceUseCase`."""

    source: str
    include_summary: bool = False


class ProcessSourceUseCase:
    """Coordinates the processing pipeline using injected ports."""

    def __init__(
        self,
        fetcher: ContentFetcher,
        extractor: ContentExtractor,
        html_to_markdown: Callable[[str], str],
        summarizer: Summarizer | None = None,
    ) -> None:
        self._fetcher = fetcher
        self._extractor = extractor
        self._html_to_markdown = html_to_markdown
        self._summarizer = summarizer

    def execute(self, cmd: ProcessSourceCommand) -> ProcessedContent:
        started = time.perf_counter()
        logger.info("Fetching source: %s", cmd.source)
        raw = self._fetcher.fetch(cmd.source)

        logger.info("Extracting readable content")
        extraction = self._extractor.extract(raw)
        title = extraction.title.strip() or "Untitled document"
        body_md = self._html_to_markdown(extraction.cleaned_html).strip()
        markdown = f"# {title}\n\n{body_md}" if body_md else f"# {title}\n"

        plain = html_to_plain_text_stub(extraction.cleaned_html)

        summary: str | None = None
        if cmd.include_summary:
            if self._summarizer is None:
                raise SummarizerConfigurationError(
                    "A Summarizer instance is required when include_summary is true.",
                )
            summary = self._summarizer.summarize(plain)
            logger.info("Summary enabled (injected Summarizer)")

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
