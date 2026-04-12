"""Extractive summarizer — no external APIs (tests / deterministic runs)."""

from __future__ import annotations

from ai_context.domain.ports import Summarizer
from ai_context.utils.plain_text import first_three_sentences


class ExtractiveSummarizer(Summarizer):
    """Return the first few sentences of the input text."""

    def summarize(self, text: str) -> str:
        return first_three_sentences(text)
