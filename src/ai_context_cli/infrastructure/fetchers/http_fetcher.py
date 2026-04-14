"""HTTP(S) :class:`~ai_context_cli.domain.ports.ContentFetcher` via ``httpx`` (sync)."""

from __future__ import annotations

import os
from typing import Final

import httpx

from ai_context_cli.domain.exceptions import NetworkError, UnsupportedFormatError
from ai_context_cli.domain.models import RawContent
from ai_context_cli.domain.ports import ContentFetcher

_DEFAULT_TIMEOUT_MS: Final[int] = 10_000
_DEFAULT_USER_AGENT: Final[str] = (
    "ai-context-cli/0.1.0 (+https://github.com/Hushout/ai-context-cli; readability pipeline)"
)


def _timeout_seconds() -> float:
    raw = os.environ.get("AI_CONTEXT_CLI_FETCH_TIMEOUT", str(_DEFAULT_TIMEOUT_MS))
    try:
        ms = int(raw)
    except ValueError:
        return _DEFAULT_TIMEOUT_MS / 1000.0
    return max(1, ms) / 1000.0


class HttpContentFetcher(ContentFetcher):
    """Fetches HTML over HTTP(S) with timeouts, redirects, and domain error mapping."""

    def __init__(
        self,
        *,
        user_agent: str = _DEFAULT_USER_AGENT,
        timeout_seconds: float | None = None,
    ) -> None:
        self._user_agent = user_agent
        self._timeout = timeout_seconds if timeout_seconds is not None else _timeout_seconds()

    def fetch(self, source: str) -> RawContent:
        if not source.startswith(("http://", "https://")):
            raise UnsupportedFormatError(
                "HttpContentFetcher only supports http(s) URLs; "
                f"got scheme or path that is not HTTP(S): {source!r}",
            )

        headers = {"User-Agent": self._user_agent}
        timeout = httpx.Timeout(self._timeout)

        with httpx.Client(timeout=timeout, headers=headers, follow_redirects=True) as client:
            response = self._perform_get(client, source)

        mime = response.headers.get("content-type", "application/octet-stream")
        mime_type = mime.split(";")[0].strip().lower() if mime else "application/octet-stream"

        return RawContent(
            source=source,
            html=response.text,
            mime_type=mime_type,
        )

    def _perform_get(self, client: httpx.Client, url: str) -> httpx.Response:
        """Perform a GET and enforce success; sync twin for a future async implementation.

        This method is intentionally small so an ``async def _perform_get`` variant can
        mirror it later using :class:`httpx.AsyncClient` without restructuring the use case.
        """

        try:
            response = client.get(url)
        except httpx.TimeoutException as exc:
            raise NetworkError(f"HTTP request timed out after {self._timeout}s", cause=exc) from exc
        except httpx.RequestError as exc:
            raise NetworkError(f"HTTP request failed: {exc}", cause=exc) from exc

        try:
            response.raise_for_status()
        except httpx.HTTPStatusError as exc:
            status = exc.response.status_code
            reason = exc.response.reason_phrase
            raise NetworkError(
                f"HTTP request failed with status {status} {reason}",
                cause=exc,
            ) from exc

        return response
