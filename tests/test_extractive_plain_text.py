"""Tests for plain-text helpers (moved from application stub)."""

from __future__ import annotations

from ai_context.utils.plain_text import first_three_sentences, html_to_plain_text_stub


def test_html_to_plain_text_stub_strips_tags() -> None:
    html = "<p>Hello <b>world</b>.</p>"
    assert html_to_plain_text_stub(html) == "Hello world."


def test_first_three_sentences_caps_at_three() -> None:
    text = "One. Two! Three? Four."
    got = first_three_sentences(text)
    assert "One." in got and "Two!" in got and "Three?" in got
    assert "Four." not in got
