"""LiteLLM-backed summarizer — imports *litellm* only inside :meth:`summarize`."""

from __future__ import annotations

from ai_context.domain.exceptions import (
    ParseError,
    SummarizerAuthenticationError,
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

_AUTH_HELP = (
    "LLM authentication failed. Set the API key your provider expects "
    "(e.g. OPENROUTER_API_KEY for openrouter/…, OPENAI_API_KEY for OpenAI, "
    "ANTHROPIC_API_KEY for anthropic/…). See LiteLLM provider docs."
)


def _map_provider_error(exc: BaseException) -> None:
    """Map LiteLLM / HTTP client failures to domain errors (imports litellm lazily)."""

    auth_types: tuple[type[BaseException], ...] = ()
    rate_types: tuple[type[BaseException], ...] = ()
    try:
        from litellm.exceptions import (  # noqa: I001, PLC0415
            AuthenticationError as LitellmAuthenticationError,
            RateLimitError as LitellmRateLimitError,
        )

        auth_types = (LitellmAuthenticationError,)
        rate_types = (LitellmRateLimitError,)
    except ImportError:
        pass

    if auth_types and isinstance(exc, auth_types):
        raise SummarizerAuthenticationError(_AUTH_HELP) from exc

    name = type(exc).__name__
    lower = str(exc).lower()
    if "AuthenticationError" in name or "authentication" in lower or "invalid api key" in lower:
        raise SummarizerAuthenticationError(_AUTH_HELP) from exc
    if rate_types and isinstance(exc, rate_types):
        raise SummarizerRateLimitError(f"LLM rate limit exceeded: {exc}") from exc
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
