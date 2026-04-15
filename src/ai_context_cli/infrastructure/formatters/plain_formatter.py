"""Plain text output formatter."""

from __future__ import annotations

import re

from ai_context_cli.domain.models import ProcessedContent
from ai_context_cli.domain.ports import OutputFormatter

_HEADING_PREFIX_RE = re.compile(r"^\s{0,3}#{1,6}\s?", re.MULTILINE)
_LINK_RE = re.compile(r"\[([^\]]+)\]\(([^)]+)\)")
_INLINE_CODE_RE = re.compile(r"`([^`]+)`")
_EMPHASIS_RE = re.compile(r"(\*\*|__|\*|_)([^*_]+)\1")


class PlainFormatter(OutputFormatter):
    """Serialize pipeline output as plain text."""

    def format(self, content: ProcessedContent) -> str:
        text = content.markdown
        text = _HEADING_PREFIX_RE.sub("", text)
        text = _LINK_RE.sub(r"\1 (\2)", text)
        text = _INLINE_CODE_RE.sub(r"\1", text)
        text = _EMPHASIS_RE.sub(r"\2", text)
        text = text.rstrip()
        if content.summary is None:
            return f"{text}\n"
        return f"{text}\n\nSummary\n\n{content.summary.strip()}\n"
