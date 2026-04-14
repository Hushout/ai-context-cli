"""Unit tests for :class:`~ai_context_cli.infrastructure.summarizers.LiteLLMSummarizer`."""

from __future__ import annotations

import pytest

from ai_context_cli.domain.exceptions import (
    ParseError,
    SummarizerAuthenticationError,
    SummarizerInvocationError,
    SummarizerRateLimitError,
)
from ai_context_cli.infrastructure.summarizers.litellm_summarizer import LiteLLMSummarizer


def test_empty_text_raises_parse_error() -> None:
    summarizer = LiteLLMSummarizer("gpt-4o-mini")
    with pytest.raises(ParseError):
        summarizer.summarize("   \n")


def test_openrouter_calls_completion_without_openai_key(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """No pre-flight env check: LiteLLM runs (here mocked) even without OPENAI_API_KEY."""

    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)
    seen: list[str] = []

    def fake_completion(**kwargs: object) -> object:
        seen.append(str(kwargs.get("model", "")))

        class _Msg:
            content = "ok"

        class _Choice:
            message = _Msg()

        class _Resp:
            choices = [_Choice()]

        return _Resp()

    import litellm

    monkeypatch.setattr(litellm, "completion", fake_completion)
    summarizer = LiteLLMSummarizer("openrouter/openai/gpt-4o-mini")
    assert summarizer.summarize("hi") == "ok"
    assert seen == ["openrouter/openai/gpt-4o-mini"]


def test_ollama_calls_completion(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)

    def fake_completion(**_kwargs: object) -> object:
        class _Msg:
            content = "Local summary."

        class _Choice:
            message = _Msg()

        class _Resp:
            choices = [_Choice()]

        return _Resp()

    import litellm

    monkeypatch.setattr(litellm, "completion", fake_completion)
    summarizer = LiteLLMSummarizer("ollama/llama3")
    assert summarizer.summarize("Hi.") == "Local summary."


def test_litellm_authentication_error_mapped(monkeypatch: pytest.MonkeyPatch) -> None:
    from litellm.exceptions import AuthenticationError

    def boom(**_kwargs: object) -> None:
        raise AuthenticationError("invalid", llm_provider="openrouter", model="x", response=None)

    import litellm

    monkeypatch.setattr(litellm, "completion", boom)
    summarizer = LiteLLMSummarizer("openrouter/openai/gpt-4o-mini")
    with pytest.raises(SummarizerAuthenticationError) as excinfo:
        summarizer.summarize("text")
    assert "OPENROUTER_API_KEY" in str(excinfo.value)


def test_completion_auth_failure_string_fallback_mapped(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def boom(**_kwargs: object) -> None:
        raise RuntimeError("AuthenticationError: invalid api key")

    import litellm

    monkeypatch.setattr(litellm, "completion", boom)
    summarizer = LiteLLMSummarizer("gpt-4o-mini")
    with pytest.raises(SummarizerAuthenticationError):
        summarizer.summarize("text")


def test_completion_rate_limit_mapped(monkeypatch: pytest.MonkeyPatch) -> None:
    def boom(**_kwargs: object) -> None:
        raise RuntimeError("rate limit exceeded (429)")

    import litellm

    monkeypatch.setattr(litellm, "completion", boom)
    summarizer = LiteLLMSummarizer("gpt-4o-mini")
    with pytest.raises(SummarizerRateLimitError):
        summarizer.summarize("text")


def test_litellm_rate_limit_error_mapped(monkeypatch: pytest.MonkeyPatch) -> None:
    from litellm.exceptions import RateLimitError

    def boom(**_kwargs: object) -> None:
        raise RateLimitError("slow down", llm_provider="openai", model="x", response=None)

    import litellm

    monkeypatch.setattr(litellm, "completion", boom)
    summarizer = LiteLLMSummarizer("gpt-4o-mini")
    with pytest.raises(SummarizerRateLimitError):
        summarizer.summarize("text")


def test_completion_success(monkeypatch: pytest.MonkeyPatch) -> None:
    def fake_completion(**_kwargs: object) -> object:
        class _Msg:
            content = "Done."

        class _Choice:
            message = _Msg()

        class _Resp:
            choices = [_Choice()]

        return _Resp()

    import litellm

    monkeypatch.setattr(litellm, "completion", fake_completion)
    summarizer = LiteLLMSummarizer("gpt-4o-mini")
    assert summarizer.summarize("Some body.") == "Done."


def test_empty_llm_response_raises(monkeypatch: pytest.MonkeyPatch) -> None:
    def fake_completion(**_kwargs: object) -> object:
        class _Msg:
            content = "  "

        class _Choice:
            message = _Msg()

        class _Resp:
            choices = [_Choice()]

        return _Resp()

    import litellm

    monkeypatch.setattr(litellm, "completion", fake_completion)
    summarizer = LiteLLMSummarizer("gpt-4o-mini")
    with pytest.raises(SummarizerInvocationError):
        summarizer.summarize("nonempty")
