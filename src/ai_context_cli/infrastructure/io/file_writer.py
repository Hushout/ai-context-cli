"""Filesystem writer for formatted output."""

from __future__ import annotations

from pathlib import Path

from ai_context_cli.domain.exceptions import OutputError


class FileWriter:
    """Write text output to a local file path."""

    def write_text(self, target: Path, content: str) -> None:
        try:
            if not target.parent.exists():
                target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(content, encoding="utf-8")
        except OSError as exc:
            raise OutputError(f"Unable to write output file: {target}", cause=exc) from exc
