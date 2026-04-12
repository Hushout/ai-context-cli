"""LiteLLM-backed summarizer — imports *litellm* only inside :meth:`summarize`."""

from __future__ import annotations

import os

from ai_context.domain.exceptions import (
    ParseError,
    SummarizerAuthenticationError,
    SummarizerConfigurationError,
    SummarizerInvocationError,
    SummarizerRateLimitError,
)
from ai_context.domain.ports import Summarizer

_SYSTEM_PROMPT = (
    "You summarize article body text that may be Markdown or plain text. "
    "Return a tight summary of the key points (short paragraph or 3–6 bullet "
    "lines). Match the source language when it is obvious. "
    "Do not prepend labels like 'Summary:'."
)

_MAX_INPUT_CHARS = 120_000


def _require_provider_credentials(model: str) -> None:
    m = model.lower().strip()
    if m.startswith("ollama/") or m.startswith("ollama_chat/"):
        return
    if m.startswith("anthropic/"):
        if not os.environ.get("ANTHROPIC_API_KEY"):
            raise SummarizerConfigurationError(
                "Missing ANTHROPIC_API_KEY in the environment (or .env) for this model.",
            )
        return
    if m.startswith("mistral/") or m.startswith("mistralai/"):
        if not os.environ.get("MISTRAL_API_KEY"):
            raise SummarizerConfigurationError(
                "Missing MISTRAL_API_KEY in the environment (or .env) for this model.",
            )
        return
    if not os.environ.get("OPENAI_API_KEY"):
        raise SummarizerConfigurationError(
            "Missing OPENAI_API_KEY in the environment (or .env). "
            "OpenAI-compatible models (e.g. gpt-4o-mini) require this variable.",
        )


def _map_provider_error(exc: BaseException) -> None:
    name = type(exc).__name__
    lower = str(exc).lower()
    if "AuthenticationError" in name or "authentication" in lower or "invalid api key" in lower:
        raise SummarizerAuthenticationError(f"LLM authentication failed: {exc}") from exc
    if "RateLimit" in name or "rate limit" in lower or "429" in lower:
        raise SummarizerRateLimitError(f"LLM rate limit exceeded: {exc}") from exc
    raise SummarizerInvocationError(f"LLM summarization failed: {exc}") from exc


class LiteLLMSummarizer(Summarizer):
    """Summarize via LiteLLM; heavy imports are deferred until :meth:`summarize`."""

    def __init__(self, model: str, *, timeout_seconds: float = 30.0) -> None:
        self._model = model
        self._timeout = timeout_seconds

    def summarize(self, text: str) -> str:
        if not text.strip():
            raise ParseError("Cannot summarize empty document text.")

        _require_provider_credentials(self._model)

        from litellm import completion  # noqa: PLC0415 — lazy import (cold start)

        payload = text if len(text) <= _MAX_INPUT_CHARS else text[:_MAX_INPUT_CHARS]

        try:
            response = completion(
                model=self._model,
                messages=[
                    {"role": "system", "content": _SYSTEM_PROMPT},
                    {"role": "user", "content": payload},
                ],
                timeout=self._timeout,
            )
        except Exception as exc:  # noqa: BLE001 — narrowed via _map_provider_error
            _map_provider_error(exc)

        try:
            choices = response["choices"] if isinstance(response, dict) else response.choices
            first = choices[0]
            message = first["message"] if isinstance(first, dict) else first.message
            content = message["content"] if isinstance(message, dict) else message.content
        except (AttributeError, IndexError, KeyError, TypeError) as exc:
            raise SummarizerInvocationError("Unexpected LLM response shape.") from exc

        if content is None or not str(content).strip():
            raise SummarizerInvocationError("LLM returned an empty summary.")
        return str(content).strip()
