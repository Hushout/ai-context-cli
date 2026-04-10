"""Domain ports (abstract interfaces).

These are the boundaries between the domain and the infrastructure layer.
Each port is a pure ABC — no concrete implementation, no infrastructure import.
Infrastructure adapters implement these contracts; the application layer
depends only on these abstractions (Dependency Inversion Principle).
"""

from __future__ import annotations

from abc import ABC, abstractmethod

from .models import ProcessedContent, RawContent


class ContentFetcher(ABC):
    """Retrieve raw content from a source (URL or file path).

    Implementations: HttpFetcher, FileFetcher.
    """

    @abstractmethod
    def fetch(self, source: str) -> RawContent:
        """Fetch content from *source* and return it as a RawContent value object.

        Args:
            source: A URL (``https://...``) or an absolute/relative file path.

        Returns:
            A :class:`~ai_context.domain.models.RawContent` instance.

        Raises:
            ~ai_context.domain.exceptions.NetworkError: On HTTP failure or timeout.
            ~ai_context.domain.exceptions.SourceNotFoundError: If the file does not exist.
            ~ai_context.domain.exceptions.UnsupportedFormatError: If the MIME type is unsupported.
        """
        ...


class ContentExtractor(ABC):
    """Extract the readable body from raw content.

    Strips navigation, ads, sidebars, and other boilerplate.
    Returns clean HTML ready for Markdown conversion.

    Implementations: ReadabilityExtractor.
    """

    @abstractmethod
    def extract(self, raw: RawContent) -> str:
        """Extract the main article body from *raw* content.

        Args:
            raw: A :class:`~ai_context.domain.models.RawContent` instance.

        Returns:
            A clean HTML string containing only the main content.

        Raises:
            ~ai_context.domain.exceptions.ParseError: If no readable content is found.
        """
        ...


class Summarizer(ABC):
    """Produce a concise summary of the given text.

    Implementations: ExtractiveSummarizer (v1), LlmSummarizer (v1.1+).
    """

    @abstractmethod
    def summarize(self, text: str) -> str:
        """Summarize *text* and return a shorter representation.

        Args:
            text: Plain text or Markdown string to summarize.

        Returns:
            A summary string (shorter than the input).

        Raises:
            ~ai_context.domain.exceptions.ParseError: If the input is empty or unsummarisable.
        """
        ...


class OutputFormatter(ABC):
    """Serialize a :class:`~ai_context.domain.models.ProcessedContent` to a string.

    Implementations: MarkdownFormatter, JsonFormatter, YamlFormatter, AllFormatter.
    """

    @abstractmethod
    def format(self, content: ProcessedContent) -> str:
        """Serialize *content* to the target format.

        Args:
            content: A fully processed :class:`~ai_context.domain.models.ProcessedContent`.

        Returns:
            A formatted string ready to be written to stdout or a file.

        Raises:
            ~ai_context.domain.exceptions.OutputError: On serialization failure.
        """
        ...
