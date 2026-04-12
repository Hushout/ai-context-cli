"""Unit tests for :class:`~ai_context.infrastructure.summarizers.LiteLLMSummarizer`."""

from __future__ import annotations

import pytest

from ai_context.domain.exceptions import (
    ParseError,
    SummarizerAuthenticationError,
    SummarizerConfigurationError,
    SummarizerInvocationError,
    SummarizerRateLimitError,
)
from ai_context.infrastructure.summarizers.litellm_summarizer import LiteLLMSummarizer


def test_empty_text_raises_parse_error() -> None:
    summarizer = LiteLLMSummarizer("gpt-4o-mini")
    with pytest.raises(ParseError):
        summarizer.summarize("   \n")


def test_missing_openai_key(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    summarizer = LiteLLMSummarizer("gpt-4o-mini")
    with pytest.raises(SummarizerConfigurationError):
        summarizer.summarize("Hello there.")


def test_missing_anthropic_key(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    summarizer = LiteLLMSummarizer("anthropic/claude-3-haiku-20240307")
    with pytest.raises(SummarizerConfigurationError):
        summarizer.summarize("x")


def test_missing_mistral_key(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("MISTRAL_API_KEY", raising=False)
    summarizer = LiteLLMSummarizer("mistral/mistral-small-latest")
    with pytest.raises(SummarizerConfigurationError):
        summarizer.summarize("x")


def test_ollama_skips_api_key_check(monkeypatch: pytest.MonkeyPatch) -> None:
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


def test_completion_auth_failure_mapped(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("OPENAI_API_KEY", "sk-test")

    def boom(**_kwargs: object) -> None:
        raise RuntimeError("AuthenticationError: invalid api key")

    import litellm

    monkeypatch.setattr(litellm, "completion", boom)
    summarizer = LiteLLMSummarizer("gpt-4o-mini")
    with pytest.raises(SummarizerAuthenticationError):
        summarizer.summarize("text")


def test_completion_rate_limit_mapped(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("OPENAI_API_KEY", "sk-test")

    def boom(**_kwargs: object) -> None:
        raise RuntimeError("rate limit exceeded (429)")

    import litellm

    monkeypatch.setattr(litellm, "completion", boom)
    summarizer = LiteLLMSummarizer("gpt-4o-mini")
    with pytest.raises(SummarizerRateLimitError):
        summarizer.summarize("text")


def test_completion_success(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("OPENAI_API_KEY", "sk-test")

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
    monkeypatch.setenv("OPENAI_API_KEY", "sk-test")

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
