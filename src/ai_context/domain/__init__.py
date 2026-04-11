"""Domain layer — pure business logic, no infrastructure dependencies."""

from .exceptions import (
    AiContextError,
    NetworkError,
    OutputError,
    ParseError,
    SourceNotFoundError,
    UnsupportedFormatError,
)
from .models import (
    ContentMeta,
    ContentStructure,
    ExtractedContent,
    ProcessedContent,
    RawContent,
    Section,
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
]
