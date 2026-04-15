"""Tests for token estimation and Markdown truncation helpers."""

from __future__ import annotations

from ai_context_cli.utils.plain_text import (
    MARKDOWN_TRUNCATION_FOOTER,
    estimate_tokens_from_text,
    truncate_markdown_to_token_budget,
)


def test_estimate_tokens_matches_chars_over_four_and_word_floor() -> None:
    text = "a" * 40
    assert estimate_tokens_from_text(text) == 10
    assert estimate_tokens_from_text("one two three four five") == 5


def test_truncate_noop_when_under_budget() -> None:
    md = "# Hello\n\nShort."
    out, truncated = truncate_markdown_to_token_budget(md, 10_000)
    assert out == md
    assert truncated is False


def test_truncate_none_means_no_limit() -> None:
    long_md = "# x\n\n" + ("word " * 500)
    out, truncated = truncate_markdown_to_token_budget(long_md, None)
    assert out == long_md
    assert truncated is False


def test_truncate_appends_footer_when_over_budget() -> None:
    long_md = "# Title\n\n" + ("paragraph " * 2000)
    out, truncated = truncate_markdown_to_token_budget(long_md, 50)
    assert truncated is True
    assert MARKDOWN_TRUNCATION_FOOTER.strip() in out
    assert estimate_tokens_from_text(out) <= 50
