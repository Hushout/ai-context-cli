"""URL-only source validation for early tickets (HUX-5)."""

from __future__ import annotations

from pydantic import HttpUrl, TypeAdapter, ValidationError

from ai_context_cli.domain.exceptions import ParseError, UnsupportedFormatError

_http_url_adapter = TypeAdapter(HttpUrl)


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
