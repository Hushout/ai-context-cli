"""Source normalization: HTTP(S) URLs or local filesystem paths."""

from __future__ import annotations

from pathlib import Path

from pydantic import HttpUrl, TypeAdapter, ValidationError

from ai_context_cli.domain.exceptions import ParseError, SourceNotFoundError, UnsupportedFormatError

_http_url_adapter = TypeAdapter(HttpUrl)


def normalize_command_source(raw: str) -> str:
    """Return a normalized URL string or resolved absolute local path.

    Raises:
        ParseError: Empty input or invalid URL/path.
        SourceNotFoundError: Local path does not exist.
        UnsupportedFormatError: Non-HTTP scheme (e.g. ``file:``) passed to URL validation.
    """

    stripped = raw.strip()
    if not stripped:
        raise ParseError("Source is empty.")

    if stripped.startswith(("http://", "https://")):
        return validate_http_url_command_source(stripped)

    path = Path(stripped).expanduser()
    try:
        resolved = path.resolve()
    except OSError as exc:
        raise ParseError(f"Invalid path: {exc}") from exc

    if not resolved.exists():
        raise SourceNotFoundError(f"Source not found: {resolved}")

    return str(resolved)


def validate_http_url_command_source(raw: str) -> str:
    """Return a normalized HTTP(S) URL string or raise a domain error.

    Raises:
        UnsupportedFormatError: If *raw* is not an ``http``/``https`` URL (e.g. file path).
        ParseError: If the URL fails :class:`~pydantic.HttpUrl` validation.
    """

    stripped = raw.strip()
    if not stripped.startswith(("http://", "https://")):
        msg = (
            "Only HTTP(S) URLs are supported in this version; "
            "local file paths and other schemes are not supported."
        )
        raise UnsupportedFormatError(msg)

    try:
        validated = _http_url_adapter.validate_python(stripped)
    except ValidationError as exc:
        raise ParseError(f"Invalid URL: {exc}") from exc

    return str(validated)
