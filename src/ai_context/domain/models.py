"""Domain Value Objects.

All models are immutable (frozen=True): once created, they cannot be mutated.
This enforces the Value Object pattern from DDD and makes them safe to pass
across layers without defensive copying.
"""

from __future__ import annotations

from datetime import datetime
from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field, model_validator

# ---------------------------------------------------------------------------
# Type aliases
# ---------------------------------------------------------------------------

HeadingLevel = Annotated[int, Field(ge=1, le=6, description="HTML heading depth (1–6)")]
NonNegativeInt = Annotated[int, Field(ge=0)]


# ---------------------------------------------------------------------------
# Input contract
# ---------------------------------------------------------------------------


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
