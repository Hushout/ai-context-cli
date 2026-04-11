"""Tests for ``html_fragment_to_markdown``."""

from __future__ import annotations

from ai_context.infrastructure.processors.markdown_converter import html_fragment_to_markdown


def test_markdownify_emits_atx_headings() -> None:
    html = "<article><h2>Section</h2><p>Body <strong>bold</strong>.</p></article>"
    md = html_fragment_to_markdown(html)
    assert "## Section" in md
    assert "Body" in md


def test_strips_wikipedia_style_beacon_img() -> None:
    html = (
        "<article><p>Text</p>"
        '<img src="https://fr.wikipedia.org/wiki/Special:CentralAutoLogin/start?type=1x1" alt="" />'
        "</article>"
    )
    md = html_fragment_to_markdown(html)
    assert "CentralAutoLogin" not in md
    assert "Text" in md


def test_keeps_normal_content_images() -> None:
    html = '<article><p>x</p><img src="https://example.com/photo.png" alt="pic" /></article>'
    md = html_fragment_to_markdown(html)
    assert "example.com/photo.png" in md
