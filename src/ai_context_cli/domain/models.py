"""Domain Value Objects.

All models are immutable (frozen=True): once created, they cannot be mutated.
This enforces the Value Object pattern from DDD and makes them safe to pass
across layers without defensive copying.
"""

from __future__ import annotations

from datetime import datetime
from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

# ---------------------------------------------------------------------------
# Type aliases
# ---------------------------------------------------------------------------

HeadingLevel = Annotated[int, Field(ge=1, le=6, description="HTML heading depth (1–6)")]
NonNegativeInt = Annotated[int, Field(ge=0)]
OutputFormat = Literal["markdown", "json", "plain"]

_EXTENSION_TO_FORMAT: dict[str, OutputFormat] = {
    ".json": "json",
    ".md": "markdown",
    ".markdown": "markdown",
    ".txt": "plain",
}


# ---------------------------------------------------------------------------
# Input contract
# ---------------------------------------------------------------------------


class ExtractedContent(BaseModel):
    """Result of article extraction: display title and HTML body without chrome."""

    model_config = ConfigDict(frozen=True)

    title: str = Field(description="Human-readable document title (may be empty)")
    cleaned_html: str = Field(
        description="Main article HTML only, suitable for Markdown conversion",
    )


class RawContent(BaseModel):
    """Raw content returned by a ContentFetcher before any processing."""

    model_config = ConfigDict(frozen=True)

    source: str = Field(description="Original URL or file path")
    html: str | None = Field(default=None, description="Raw HTML string, if available")
    text: str | None = Field(default=None, description="Plain text, if available")
    mime_type: str = Field(description="Detected MIME type, e.g. 'text/html'")

    @model_validator(mode="after")
    def _require_at_least_one_content_field(self) -> RawContent:
        if self.html is None and self.text is None:
            raise ValueError("At least one of 'html' or 'text' must be provided.")
        return self


# ---------------------------------------------------------------------------
# Structure
# ---------------------------------------------------------------------------


class Section(BaseModel):
    """A single heading section within the extracted content hierarchy."""

    model_config = ConfigDict(frozen=True)

    heading: str = Field(description="Heading text, stripped of Markdown markers")
    level: HeadingLevel
    subsections: list[Section] = Field(default_factory=list)


# Pydantic v2 requires explicit rebuild for self-referential models.
Section.model_rebuild()


class ContentStructure(BaseModel):
    """AI-readable structural representation of the extracted content."""

    model_config = ConfigDict(frozen=True)

    title: str
    sections: list[Section]
    entities: list[str] = Field(
        default_factory=list,
        description="Proper nouns and technical terms extracted from the content",
    )


# ---------------------------------------------------------------------------
# Metadata & output contract
# ---------------------------------------------------------------------------


class ContentMeta(BaseModel):
    """Processing metadata attached to every output."""

    model_config = ConfigDict(frozen=True)

    word_count: NonNegativeInt
    estimated_tokens: NonNegativeInt = Field(
        description="Rough token count (chars / 4). Approximation only."
    )
    extracted_at: datetime = Field(description="UTC timestamp of extraction")
    processing_ms: NonNegativeInt = Field(description="Total pipeline duration in milliseconds")


class OutputConfig(BaseModel):
    """User-facing output preferences independent from infrastructure."""

    model_config = ConfigDict(frozen=True)

    output_path: str | None = Field(default=None, description="Target output file path")
    format: OutputFormat = Field(default="markdown", description="Desired serialization format")


class ResolvedOutputConfig(BaseModel):
    """Result of output configuration arbitration."""

    model_config = ConfigDict(frozen=True)

    format: OutputFormat
    warning: str | None = None


def resolve_output_format(
    output_path: str | None,
    requested_format: OutputFormat,
) -> ResolvedOutputConfig:
    """Resolve effective output format and warning for extension mismatches."""

    if output_path is None:
        return ResolvedOutputConfig(format=requested_format, warning=None)

    suffix = output_path.lower().rsplit(".", maxsplit=1)
    if len(suffix) == 1:
        return ResolvedOutputConfig(format=requested_format, warning=None)

    extension = f".{suffix[1]}"
    inferred = _EXTENSION_TO_FORMAT.get(extension)
    if inferred is None:
        return ResolvedOutputConfig(format=requested_format, warning=None)
    if inferred == requested_format:
        return ResolvedOutputConfig(format=requested_format, warning=None)

    warning = (
        f"Requested --format '{requested_format}' conflicts with output extension "
        f"'{extension}'. Using '{inferred}'."
    )
    return ResolvedOutputConfig(format=inferred, warning=warning)


class ProcessedContent(BaseModel):
    """Final output of the processing pipeline. Immutable once built."""

    model_config = ConfigDict(frozen=True)

    source: str = Field(description="Original URL or file path")
    title: str
    markdown: str = Field(description="Clean Markdown representation of the content")
    summary: str | None = Field(default=None, description="Extractive or LLM summary")
    structure: ContentStructure | None = Field(
        default=None, description="AI-readable content structure"
    )
    meta: ContentMeta
