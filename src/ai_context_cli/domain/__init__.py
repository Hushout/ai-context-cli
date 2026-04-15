"""Domain layer — pure business logic, no infrastructure dependencies."""

from .exceptions import (
    AiContextError,
    NetworkError,
    OutputError,
    ParseError,
    SourceNotFoundError,
    SummarizerAuthenticationError,
    SummarizerConfigurationError,
    SummarizerInvocationError,
    SummarizerRateLimitError,
    UnsupportedFormatError,
)
from .models import (
    ContentMeta,
    ContentStructure,
    ExtractedContent,
    OutputConfig,
    OutputFormat,
    ProcessedContent,
    RawContent,
    ResolvedOutputConfig,
    Section,
    resolve_output_format,
)
from .ports import ContentExtractor, ContentFetcher, OutputFormatter, Summarizer

__all__ = [
    # models
    "ExtractedContent",
    "RawContent",
    "Section",
    "ContentStructure",
    "ContentMeta",
    "ProcessedContent",
    "OutputFormat",
    "OutputConfig",
    "ResolvedOutputConfig",
    "resolve_output_format",
    # ports
    "ContentFetcher",
    "ContentExtractor",
    "Summarizer",
    "OutputFormatter",
    # exceptions
    "AiContextError",
    "NetworkError",
    "ParseError",
    "SourceNotFoundError",
    "UnsupportedFormatError",
    "OutputError",
    "SummarizerAuthenticationError",
    "SummarizerRateLimitError",
    "SummarizerConfigurationError",
    "SummarizerInvocationError",
]
