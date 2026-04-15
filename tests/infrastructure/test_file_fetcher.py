"""Tests for :class:`~ai_context_cli.infrastructure.fetchers.file_fetcher.FileContentFetcher`."""

from __future__ import annotations

from pathlib import Path

import pytest

from ai_context_cli.domain.exceptions import ParseError, SourceNotFoundError, UnsupportedFormatError
from ai_context_cli.infrastructure.fetchers.file_fetcher import FileContentFetcher


def test_fetch_single_text_file_wraps_html(tmp_path: Path) -> None:
    path = tmp_path / "sample.py"
    path.write_text('print("hello")\n', encoding="utf-8")

    fetcher = FileContentFetcher()
    raw = fetcher.fetch(str(path))

    assert raw.mime_type == "text/html"
    assert raw.html is not None
    assert "sample.py" in raw.html
    assert "print" in raw.html
    assert raw.source == str(path.resolve())


def test_fetch_directory_aggregates_files(tmp_path: Path) -> None:
    root = tmp_path / "proj"
    root.mkdir(parents=True)
    (root / "a.txt").write_text("alpha", encoding="utf-8")
    (root / "b.txt").write_text("beta", encoding="utf-8")

    fetcher = FileContentFetcher()
    raw = fetcher.fetch(str(root))

    assert raw.html is not None
    assert "a.txt" in raw.html and "b.txt" in raw.html
    assert "alpha" in raw.html and "beta" in raw.html


def test_fetch_skips_hidden_files(tmp_path: Path) -> None:
    root = tmp_path / "tree"
    root.mkdir(parents=True)
    (root / "visible.txt").write_text("ok", encoding="utf-8")
    (root / ".hidden.txt").write_text("no", encoding="utf-8")

    fetcher = FileContentFetcher()
    raw = fetcher.fetch(str(root))

    assert "visible.txt" in raw.html
    assert ".hidden.txt" not in raw.html
    assert "no" not in raw.html


def test_fetch_missing_path_raises() -> None:
    fetcher = FileContentFetcher()
    with pytest.raises(SourceNotFoundError):
        fetcher.fetch("/nonexistent/path/that/does/not/exist/here")


def test_fetch_rejects_http_url() -> None:
    fetcher = FileContentFetcher()
    with pytest.raises(UnsupportedFormatError):
        fetcher.fetch("https://example.com/page")


def test_fetch_rejects_file_larger_than_env_limit(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("AI_CONTEXT_CLI_MAX_CONTENT_SIZE", "10")
    path = tmp_path / "big.txt"
    path.write_bytes(b"x" * 11)

    fetcher = FileContentFetcher()
    with pytest.raises(UnsupportedFormatError):
        fetcher.fetch(str(path))


def test_fetch_empty_directory_raises_parse_error(tmp_path: Path) -> None:
    root = tmp_path / "empty_dir"
    root.mkdir()

    fetcher = FileContentFetcher()
    with pytest.raises(ParseError):
        fetcher.fetch(str(root))
