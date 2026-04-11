"""CLI integration tests (stub pipeline, no network)."""

from __future__ import annotations

import sys

import pytest

from ai_context.interfaces.cli import run_app


def test_cli_rejects_file_path_with_exit_code_4(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.setattr(sys, "argv", ["ai-context", "./local.html"])
    with pytest.raises(SystemExit) as exc:
        run_app()
    assert exc.value.code == 4
    err = capsys.readouterr().err
    assert "Error:" in err


def test_cli_rejects_malformed_url_exit_code_2(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(sys, "argv", ["ai-context", "https://"])
    with pytest.raises(SystemExit) as exc:
        run_app()
    assert exc.value.code == 2


def test_cli_stub_pipeline_stdout(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.setattr(sys, "argv", ["ai-context", "https://example.com/article"])
    with pytest.raises(SystemExit) as exc:
        run_app()
    assert exc.value.code == 0
    out = capsys.readouterr().out
    assert "# Stub document" in out
    assert "First stub sentence" in out
    assert "Summary" not in out


def test_cli_summary_flag_includes_stub_summary(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.setattr(
        sys,
        "argv",
        ["ai-context", "https://example.com/article", "--summary"],
    )
    with pytest.raises(SystemExit) as exc:
        run_app()
    assert exc.value.code == 0
    out = capsys.readouterr().out
    assert "## Summary (stub)" in out
    _body, summary_block = out.split("## Summary (stub)", maxsplit=1)
    assert "Fourth stub sentence" in _body  # full stub body still lists all sentences
    assert "Fourth stub sentence" not in summary_block
