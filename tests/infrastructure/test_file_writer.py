"""Tests for file output writer."""

from __future__ import annotations

from pathlib import Path

from ai_context_cli.infrastructure.io import FileWriter


def test_file_writer_creates_missing_parent_directories(tmp_path: Path) -> None:
    output_path = tmp_path / "nested" / "result.md"
    FileWriter().write_text(output_path, "hello")
    assert output_path.read_text(encoding="utf-8") == "hello"
