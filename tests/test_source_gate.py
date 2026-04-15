"""Tests for source normalization (URL and local path)."""

from __future__ import annotations

from pathlib import Path

import pytest
from pydantic import ValidationError

from ai_context_cli.application.source_gate import (
    normalize_command_source,
    validate_http_url_command_source,
)
from ai_context_cli.domain.exceptions import ParseError, SourceNotFoundError, UnsupportedFormatError


def test_rejects_local_path() -> None:
    with pytest.raises(UnsupportedFormatError):
        validate_http_url_command_source("./README.md")


def test_rejects_windows_path() -> None:
    with pytest.raises(UnsupportedFormatError):
        validate_http_url_command_source(r"C:\temp\file.html")


def test_rejects_non_http_scheme() -> None:
    with pytest.raises(UnsupportedFormatError):
        validate_http_url_command_source("file:///etc/passwd")


def test_accepts_https_url() -> None:
    assert (
        validate_http_url_command_source("  https://example.com/path  ")
        == "https://example.com/path"
    )


def test_invalid_http_url_raises_parse_error() -> None:
    with pytest.raises(ParseError) as excinfo:
        validate_http_url_command_source("https://")

    assert isinstance(excinfo.value.__cause__, ValidationError)


def test_normalize_accepts_existing_file(tmp_path: Path) -> None:
    path = tmp_path / "note.txt"
    path.write_text("hello", encoding="utf-8")
    out = normalize_command_source(str(path))
    assert Path(out) == path.resolve()


def test_normalize_rejects_missing_local_path() -> None:
    with pytest.raises(SourceNotFoundError):
        normalize_command_source("/nonexistent/path/zzzz-no-such-file")


def test_normalize_empty_source_raises() -> None:
    with pytest.raises(ParseError):
        normalize_command_source("   ")


def test_normalize_https_same_as_validate() -> None:
    assert normalize_command_source(
        "  https://example.com/x  "
    ) == validate_http_url_command_source("  https://example.com/x  ")
