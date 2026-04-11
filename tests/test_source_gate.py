"""Tests for URL-only source validation."""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from ai_context.application.source_gate import validate_http_url_command_source
from ai_context.domain.exceptions import ParseError, UnsupportedFormatError


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
    assert validate_http_url_command_source("  https://example.com/path  ") == "https://example.com/path"


def test_invalid_http_url_raises_parse_error() -> None:
    with pytest.raises(ParseError) as excinfo:
        validate_http_url_command_source("https://")

    assert isinstance(excinfo.value.__cause__, ValidationError)
