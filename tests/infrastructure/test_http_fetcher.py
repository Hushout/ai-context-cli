"""Tests for :class:`~ai_context_cli.infrastructure.fetchers.http_fetcher.HttpContentFetcher`."""

from __future__ import annotations

import httpx
import pytest
from pytest_httpx import HTTPXMock

from ai_context_cli.domain.exceptions import NetworkError, UnsupportedFormatError
from ai_context_cli.infrastructure.fetchers.http_fetcher import HttpContentFetcher


def test_fetch_rejects_non_http_url() -> None:
    with pytest.raises(UnsupportedFormatError):
        HttpContentFetcher().fetch("/etc/passwd")


def test_fetch_maps_http_404_to_network_error(httpx_mock: HTTPXMock) -> None:
    httpx_mock.add_response(url="https://example.com/missing", status_code=404)
    with pytest.raises(NetworkError, match="404"):
        HttpContentFetcher().fetch("https://example.com/missing")


def test_fetch_maps_http_500_to_network_error(httpx_mock: HTTPXMock) -> None:
    httpx_mock.add_response(url="https://example.com/boom", status_code=500)
    with pytest.raises(NetworkError, match="500"):
        HttpContentFetcher().fetch("https://example.com/boom")


def test_fetch_succeeds_when_fetch_timeout_env_is_invalid(
    monkeypatch: pytest.MonkeyPatch, httpx_mock: HTTPXMock
) -> None:
    monkeypatch.setenv("AI_CONTEXT_CLI_FETCH_TIMEOUT", "not-a-number")
    httpx_mock.add_response(url="https://example.com/page", text="<html/>")
    raw = HttpContentFetcher().fetch("https://example.com/page")
    assert raw.html == "<html/>"


def test_fetch_maps_connect_error_to_network_error(httpx_mock: HTTPXMock) -> None:
    request = httpx.Request("GET", "https://example.com/page")
    httpx_mock.add_exception(httpx.ConnectError("connection refused", request=request))
    with pytest.raises(NetworkError, match="HTTP request failed"):
        HttpContentFetcher().fetch("https://example.com/page")


def test_fetch_success_returns_raw_content(httpx_mock: HTTPXMock) -> None:
    body = "<html><head><title>T</title></head><body><p>ok</p></body></html>"
    httpx_mock.add_response(url="https://example.com/page", text=body)
    raw = HttpContentFetcher().fetch("https://example.com/page")
    assert raw.source == "https://example.com/page"
    assert raw.html == body
    assert raw.mime_type == "text/plain"
