"""Tests for stub extractive sentence helpers."""

from __future__ import annotations

from ai_context.application.extractive_stub import first_three_sentences, html_to_plain_text_stub


def test_html_to_plain_text_stub_strips_tags() -> None:
    html = "<article><p>Hello <b>world</b>.</p></article>"
    assert html_to_plain_text_stub(html) == "Hello world."


def test_first_three_sentences_truncates() -> None:
    text = "First sentence here. Second sentence! Third one? Fourth should be dropped. Fifth too."
    got = first_three_sentences(text)
    assert "Fourth" not in got
    assert got.startswith("First sentence here.")
    assert "Third one?" in got


def test_first_three_sentences_fewer_than_three() -> None:
    assert first_three_sentences("Only one.") == "Only one."
