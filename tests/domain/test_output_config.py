"""Output format arbitration tests."""

from __future__ import annotations

from ai_context_cli.domain.models import resolve_output_format


def test_resolve_output_format_keeps_requested_without_output_file() -> None:
    resolved = resolve_output_format(output_path=None, requested_format="markdown")
    assert resolved.format == "markdown"
    assert resolved.warning is None


def test_resolve_output_format_uses_extension_when_conflicting() -> None:
    resolved = resolve_output_format(output_path="results.txt", requested_format="json")
    assert resolved.format == "plain"
    assert resolved.warning is not None
    assert "conflicts" in resolved.warning


def test_resolve_output_format_keeps_requested_with_unknown_extension() -> None:
    resolved = resolve_output_format(output_path="results.custom", requested_format="json")
    assert resolved.format == "json"
    assert resolved.warning is None


def test_resolve_output_format_uses_json_extension_without_warning() -> None:
    resolved = resolve_output_format(output_path="results.json", requested_format="json")
    assert resolved.format == "json"
    assert resolved.warning is None
