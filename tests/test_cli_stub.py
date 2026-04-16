"""CLI integration tests (stubs swapped in — no real network)."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

from ai_context_cli.domain.ports import Summarizer
from ai_context_cli.infrastructure.extractors import StubContentExtractor
from ai_context_cli.infrastructure.fetchers import StubContentFetcher
from ai_context_cli.infrastructure.summarizers import ExtractiveSummarizer
from ai_context_cli.interfaces import cli as cli_module
from ai_context_cli.interfaces.cli import run_app


def test_cli_version_flag_prints_version_and_exits(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.setattr(sys, "argv", ["ai-context-cli", "--version"])
    with pytest.raises(SystemExit) as exc:
        run_app()
    assert exc.value.code == 0
    out = capsys.readouterr().out.strip()
    assert out


def test_cli_missing_local_path_exit_code_3(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str], tmp_path: Path
) -> None:
    missing = tmp_path / "does-not-exist.html"
    monkeypatch.setattr(sys, "argv", ["ai-context-cli", str(missing)])
    with pytest.raises(SystemExit) as exc:
        run_app()
    assert exc.value.code == 3
    err = capsys.readouterr().err
    assert "Error:" in err


def test_cli_accepts_local_file_path(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str], tmp_path: Path
) -> None:
    path = tmp_path / "sample.py"
    path.write_text("# local file", encoding="utf-8")
    monkeypatch.setattr(sys, "argv", ["ai-context-cli", str(path)])
    with pytest.raises(SystemExit) as exc:
        run_app()
    assert exc.value.code == 0
    out = capsys.readouterr().out
    assert "# Stub document" in out


def test_cli_rejects_malformed_url_exit_code_2(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(sys, "argv", ["ai-context-cli", "https://"])
    with pytest.raises(SystemExit) as exc:
        run_app()
    assert exc.value.code == 2


@pytest.fixture(autouse=True)
def _cli_uses_stub_adapters(monkeypatch: pytest.MonkeyPatch) -> None:
    """Keep CLI tests deterministic (no outbound HTTP or LLM)."""

    monkeypatch.setattr(cli_module, "HttpContentFetcher", StubContentFetcher)
    monkeypatch.setattr(cli_module, "FileContentFetcher", StubContentFetcher)
    monkeypatch.setattr(cli_module, "ReadabilityExtractor", StubContentExtractor)

    def _stub_summarizer(_model: str) -> Summarizer:
        return ExtractiveSummarizer()

    monkeypatch.setattr(cli_module, "_build_summarizer_for_cli", _stub_summarizer)
    monkeypatch.setattr(cli_module, "_maybe_load_dotenv_for_summary", lambda: None)


def test_cli_stub_pipeline_stdout(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.setattr(sys, "argv", ["ai-context-cli", "https://example.com/article"])
    with pytest.raises(SystemExit) as exc:
        run_app()
    assert exc.value.code == 0
    out = capsys.readouterr().out
    assert "# Stub document" in out
    assert "First stub sentence" in out
    assert "Summary" not in out


def test_cli_summary_flag_includes_summary_block(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.setattr(
        sys,
        "argv",
        ["ai-context-cli", "https://example.com/article", "--summary"],
    )
    with pytest.raises(SystemExit) as exc:
        run_app()
    assert exc.value.code == 0
    out = capsys.readouterr().out
    assert "## Summary" in out
    _body, summary_block = out.split("## Summary", maxsplit=1)
    assert "Fourth stub sentence" in _body  # full stub body still lists all sentences
    assert "Fourth stub sentence" not in summary_block


def test_cli_structure_flag_includes_table_of_contents(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.setattr(
        sys,
        "argv",
        ["ai-context-cli", "https://example.com/article", "--structure"],
    )
    with pytest.raises(SystemExit) as exc:
        run_app()
    assert exc.value.code == 0
    out = capsys.readouterr().out
    assert "## Table of Contents" in out
    assert "- [Stub document](#stub-document)" in out


def test_cli_writes_json_output_file(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str], tmp_path: Path
) -> None:
    output_path = tmp_path / "exports" / "result.json"
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "ai-context-cli",
            "https://example.com/article",
            "--format",
            "json",
            "--output",
            str(output_path),
        ],
    )
    with pytest.raises(SystemExit) as exc:
        run_app()
    assert exc.value.code == 0
    assert capsys.readouterr().out == ""
    payload = json.loads(output_path.read_text(encoding="utf-8"))
    assert payload["source"] == "https://example.com/article"
    assert "markdown" in payload
    assert "meta" in payload


def test_cli_structure_flag_populates_json_structure(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str], tmp_path: Path
) -> None:
    output_path = tmp_path / "exports" / "result.json"
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "ai-context-cli",
            "https://example.com/article",
            "--structure",
            "--format",
            "json",
            "--output",
            str(output_path),
        ],
    )
    with pytest.raises(SystemExit) as exc:
        run_app()
    assert exc.value.code == 0
    assert capsys.readouterr().out == ""
    payload = json.loads(output_path.read_text(encoding="utf-8"))
    assert payload["structure"] is not None
    assert payload["structure"]["title"] == "Stub document"


def test_cli_warns_and_adapts_when_extension_conflicts_with_format(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str], tmp_path: Path
) -> None:
    output_path = tmp_path / "result.json"
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "ai-context-cli",
            "https://example.com/article",
            "--format",
            "markdown",
            "--output",
            str(output_path),
        ],
    )
    with pytest.raises(SystemExit) as exc:
        run_app()
    assert exc.value.code == 0
    err = capsys.readouterr().err
    assert "Warning:" in err
    payload = json.loads(output_path.read_text(encoding="utf-8"))
    assert payload["source"] == "https://example.com/article"
