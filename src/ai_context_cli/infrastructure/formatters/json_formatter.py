"""JSON output formatter."""

from __future__ import annotations

import json

from ai_context_cli.domain.exceptions import OutputError
from ai_context_cli.domain.models import ProcessedContent
from ai_context_cli.domain.ports import OutputFormatter


class JsonFormatter(OutputFormatter):
    """Serialize pipeline output as stable JSON."""

    def format(self, content: ProcessedContent) -> str:
        payload = content.model_dump(mode="json")
        try:
            return json.dumps(payload, ensure_ascii=False, indent=2)
        except TypeError as exc:  # pragma: no cover - defensive
            raise OutputError("Failed to serialize processed content as JSON.", cause=exc) from exc
