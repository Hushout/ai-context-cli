"""Tests for Markdown structure analysis."""

from __future__ import annotations

from ai_context_cli.infrastructure.processors import analyze_markdown_structure


def test_analyze_markdown_structure_builds_nested_sections() -> None:
    markdown = """# Root

## Child A

### Grandchild A1

## Child B
"""
    structure = analyze_markdown_structure(markdown, fallback_title="Fallback")
    assert structure.title == "Root"
    assert len(structure.sections) == 1
    root = structure.sections[0]
    assert root.heading == "Root"
    assert root.level == 1
    assert [child.heading for child in root.subsections] == ["Child A", "Child B"]
    assert root.subsections[0].subsections[0].heading == "Grandchild A1"


def test_analyze_markdown_structure_ignores_fenced_code_blocks() -> None:
    markdown = """# Root

```md
## Not a real heading
```

## Real heading
"""
    structure = analyze_markdown_structure(markdown, fallback_title="Fallback")
    assert len(structure.sections) == 1
    root = structure.sections[0]
    assert [child.heading for child in root.subsections] == ["Real heading"]


def test_analyze_markdown_structure_uses_fallback_title_when_missing_h1() -> None:
    markdown = """Plain paragraph.

## Child only
"""
    structure = analyze_markdown_structure(markdown, fallback_title="Fallback title")
    assert structure.title == "Fallback title"
    assert len(structure.sections) == 1
    assert structure.sections[0].heading == "Child only"
