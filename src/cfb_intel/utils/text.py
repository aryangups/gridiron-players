"""Text normalization and lightweight classification."""

from __future__ import annotations

import hashlib
import re
import unicodedata

SUFFIXES = {"jr", "sr", "ii", "iii", "iv", "v"}

INJURY_KEYWORDS = {
    "injury",
    "injured",
    "questionable",
    "probable",
    "doubtful",
    "out",
    "surgery",
    "ankle",
    "knee",
    "shoulder",
    "hamstring",
}
TRANSFER_KEYWORDS = {"transfer", "portal", "commits", "commitment", "decommit"}
PERFORMANCE_KEYWORDS = {"yards", "touchdowns", "breakout", "record", "award"}
DEPTH_KEYWORDS = {"starter", "backup", "depth chart", "qb1"}
DRAFT_KEYWORDS = {"nfl draft", "scouting", "prospect"}


def normalize_name(name: str) -> str:
    text = unicodedata.normalize("NFKD", name).encode("ascii", "ignore").decode("ascii")
    text = re.sub(r"[^a-zA-Z0-9\s-]", " ", text).lower()
    parts = [part for part in re.split(r"\s+", text.strip()) if part and part not in SUFFIXES]
    return " ".join(parts)


def stable_hash(*parts: str, length: int = 16) -> str:
    joined = "|".join(normalize_name(part) for part in parts if part)
    return hashlib.sha256(joined.encode("utf-8")).hexdigest()[:length]


def split_name(full_name: str) -> tuple[str | None, str | None]:
    parts = full_name.split()
    if not parts:
        return None, None
    if len(parts) == 1:
        return parts[0], None
    return parts[0], parts[-1]


def classify_news(text: str) -> list[str]:
    lowered = text.lower()
    tags: list[str] = []
    if any(keyword in lowered for keyword in INJURY_KEYWORDS):
        tags.append("injury")
    if any(keyword in lowered for keyword in TRANSFER_KEYWORDS):
        tags.append("transfer")
    if any(keyword in lowered for keyword in PERFORMANCE_KEYWORDS):
        tags.append("performance")
    if any(keyword in lowered for keyword in DEPTH_KEYWORDS):
        tags.append("depth_chart")
    if any(keyword in lowered for keyword in DRAFT_KEYWORDS):
        tags.append("draft")
    return tags or ["general"]


def short_summary(text: str | None, max_chars: int = 280) -> str | None:
    if not text:
        return None
    cleaned = re.sub(r"\s+", " ", text).strip()
    if len(cleaned) <= max_chars:
        return cleaned
    return cleaned[: max_chars - 3].rstrip() + "..."

