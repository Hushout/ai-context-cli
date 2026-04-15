"""Local file/directory :class:`~ai_context_cli.domain.ports.ContentFetcher` via ``pathlib``."""

from __future__ import annotations

import html
import os
from pathlib import Path
from typing import Final

from ai_context_cli.domain.exceptions import ParseError, SourceNotFoundError, UnsupportedFormatError
from ai_context_cli.domain.models import RawContent
from ai_context_cli.domain.ports import ContentFetcher

_DEFAULT_MAX_BYTES: Final[int] = 2 * 1024 * 1024
_ENV_MAX_BYTES: Final[str] = "AI_CONTEXT_CLI_MAX_CONTENT_SIZE"
_BINARY_SNIFF_LEN: Final[int] = 8192


def _max_content_bytes() -> int:
    raw = os.environ.get(_ENV_MAX_BYTES, str(_DEFAULT_MAX_BYTES))
    try:
        n = int(raw)
    except ValueError:
        return _DEFAULT_MAX_BYTES
    return max(1, n)


def _is_probably_binary(raw: bytes) -> bool:
    sample = raw[:_BINARY_SNIFF_LEN]
    return b"\x00" in sample


def _read_utf8_text(path: Path, max_bytes: int) -> str:
    try:
        size = path.stat().st_size
    except OSError as exc:
        raise SourceNotFoundError(f"Cannot access path: {path}", cause=exc) from exc

    if size > max_bytes:
        raise UnsupportedFormatError(
            f"File exceeds {_ENV_MAX_BYTES} ({max_bytes} bytes): {path}",
        )

    try:
        raw = path.read_bytes()
    except OSError as exc:
        raise UnsupportedFormatError(f"Cannot read file: {path}", cause=exc) from exc

    if _is_probably_binary(raw):
        raise UnsupportedFormatError(f"Binary file not supported: {path}")

    try:
        return raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise UnsupportedFormatError(f"File is not valid UTF-8 text: {path}") from exc


def _wrap_as_article_html(*, document_title: str, body: str) -> str:
    safe_title = html.escape(document_title, quote=True)
    safe_body = html.escape(body, quote=False)
    return (
        '<!DOCTYPE html><html lang="en"><head>'
        f'<meta charset="utf-8"/><title>{safe_title}</title></head><body>'
        f"<article><h1>{safe_title}</h1><pre><code>{safe_body}</code></pre></article>"
        "</body></html>"
    )


def _wrap_directory_html(sections: list[tuple[str, str]]) -> str:
    pieces: list[str] = [
        '<!DOCTYPE html><html lang="en"><head>',
        '<meta charset="utf-8"/><title>Aggregated sources</title></head><body>',
    ]
    for rel, body in sections:
        safe_rel = html.escape(rel, quote=True)
        safe_body = html.escape(body, quote=False)
        pieces.append(
            f"<article><h1>{safe_rel}</h1><pre><code>{safe_body}</code></pre></article>",
        )
    pieces.append("</body></html>")
    return "\n".join(pieces)


def _should_skip_path(path: Path, root: Path) -> bool:
    try:
        rel = path.relative_to(root)
    except ValueError:
        return True
    return any(part.startswith(".") for part in rel.parts) or "__pycache__" in rel.parts


def _iter_candidate_files(root: Path) -> list[Path]:
    if not root.is_dir():
        return []
    out: list[Path] = []
    for p in sorted(root.rglob("*")):
        if not p.is_file():
            continue
        if _should_skip_path(p, root):
            continue
        out.append(p)
    return out


class FileContentFetcher(ContentFetcher):
    """Loads UTF-8 text from a file or aggregates text files under a directory."""

    def fetch(self, source: str) -> RawContent:
        if source.startswith(("http://", "https://")):
            raise UnsupportedFormatError(
                "FileContentFetcher only supports local paths; got a URL.",
            )

        path = Path(source)
        try:
            resolved = path.resolve()
        except OSError as exc:
            raise ParseError(f"Invalid path: {exc}") from exc

        if not resolved.exists():
            raise SourceNotFoundError(f"Source not found: {resolved}")

        max_bytes = _max_content_bytes()

        if resolved.is_file():
            text = _read_utf8_text(resolved, max_bytes)
            title = resolved.name
            html_doc = _wrap_as_article_html(document_title=title, body=text)
            return RawContent(
                source=str(resolved),
                html=html_doc,
                mime_type="text/html",
            )

        if resolved.is_dir():
            return self._fetch_directory(resolved, max_bytes)

        raise UnsupportedFormatError(f"Not a file or directory: {resolved}")

    def _fetch_directory(self, root: Path, max_bytes: int) -> RawContent:
        candidates = _iter_candidate_files(root)
        sections: list[tuple[str, str]] = []
        remaining = max_bytes

        for file_path in candidates:
            try:
                size = file_path.stat().st_size
            except OSError:
                continue
            if size > max_bytes:
                raise UnsupportedFormatError(
                    f"File exceeds {_ENV_MAX_BYTES} ({max_bytes} bytes): {file_path}",
                )
            if size > remaining:
                continue
            try:
                text = _read_utf8_text(file_path, max_bytes)
            except UnsupportedFormatError:
                continue
            rel = str(file_path.relative_to(root)).replace("\\", "/")
            sections.append((rel, text))
            remaining -= size

        if not sections:
            raise ParseError(f"No readable UTF-8 text files found under {root}")

        html_doc = _wrap_directory_html(sections)
        return RawContent(
            source=str(root.resolve()),
            html=html_doc,
            mime_type="text/html",
        )
