"""Domain exceptions.

All exceptions inherit from AiContextError so callers can catch the entire
hierarchy with a single except clause when needed.

Exit code conventions (used by the CLI error handler):
    NetworkError          → 1
    ParseError            → 2
    SourceNotFoundError   → 3
    UnsupportedFormatError → 4
    OutputError           → 5

Note: this module intentionally avoids naming any exception ``FileNotFoundError``
to prevent shadowing the Python builtin of the same name.
"""

from __future__ import annotations


class AiContextError(Exception):
    """Base exception for all ai-context-cli domain errors."""

    exit_code: int = 99

    def __init__(self, message: str, *, cause: BaseException | None = None) -> None:
        super().__init__(message)
        self.__cause__ = cause


class NetworkError(AiContextError):
    """Raised when an HTTP request fails (timeout, DNS failure, non-2xx status)."""

    exit_code = 1


class ParseError(AiContextError):
    """Raised when content cannot be parsed or yields no usable output."""

    exit_code = 2


class SourceNotFoundError(AiContextError):
    """Raised when the requested local file does not exist."""

    exit_code = 3


class UnsupportedFormatError(AiContextError):
    """Raised when the source MIME type or file extension is not supported."""

    exit_code = 4


class OutputError(AiContextError):
    """Raised when the formatted result cannot be written to the target path."""

    exit_code = 5


class SummarizerAuthenticationError(AiContextError):
    """Raised when the LLM provider rejects credentials."""

    exit_code = 6


class SummarizerRateLimitError(AiContextError):
    """Raised when the LLM provider applies a rate limit."""

    exit_code = 7


class SummarizerConfigurationError(AiContextError):
    """Raised when summarization is misconfigured (e.g. missing API key)."""

    exit_code = 8


class SummarizerInvocationError(AiContextError):
    """Raised for other LLM/runtime failures during summarization."""

    exit_code = 9
