"""HTML fragment → Markdown using ``markdownify``."""

from __future__ import annotations

import re

from markdownify import markdownify as _markdownify

# Tracking / SSO beacon images (e.g. Wikipedia 1×1 CentralAutoLogin) add noise only.
_IMG_TAG_RE = re.compile(r"<img\b[^>]*>", re.IGNORECASE)


def _strip_beacon_image_tags(html: str) -> str:
    """Remove ``<img>`` tags that are known non-content beacons before Markdown conversion."""

    def repl(match: re.Match[str]) -> str:
        tag = match.group(0)
        lower = tag.lower()
        if "centralautologin" in lower:
            return ""
        if "type=1x1" in lower or "type%3d1x1" in lower:
            return ""
        return tag

    return _IMG_TAG_RE.sub(repl, html)


def html_fragment_to_markdown(html: str) -> str:
    """Convert article HTML to GitHub-flavoured style Markdown (ATX headings, ``-`` lists)."""

    cleaned = _strip_beacon_image_tags(html)
    return _markdownify(
        cleaned,
        heading_style="ATX",
        bullets="-",
        strip=["script", "style"],
    )
