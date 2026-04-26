"""Extract conservative injury updates from injury-tagged news metadata."""

from __future__ import annotations

from cfb_intel.schemas import InjuryUpdate, NewsItem
from cfb_intel.utils.text import stable_hash

STATUS_KEYWORDS = [
    ("season-ending", "season-ending"),
    ("questionable", "questionable"),
    ("probable", "probable"),
    ("doubtful", "doubtful"),
    ("day-to-day", "day-to-day"),
    (" out ", "out"),
]

BODY_PARTS = ["ankle", "knee", "shoulder", "hamstring"]


def _status(text: str) -> str:
    lowered = f" {text.lower()} "
    for keyword, status in STATUS_KEYWORDS:
        if keyword in lowered:
            return status
    return "unknown"


def _body_part(text: str) -> str | None:
    lowered = text.lower()
    for part in BODY_PARTS:
        if part in lowered:
            return part
    return None


def extract_injuries(news_items: list[NewsItem]) -> list[InjuryUpdate]:
    injuries: list[InjuryUpdate] = []
    for item in news_items:
        if "injury" not in item.tags:
            continue
        summary_text = item.summary or item.headline
        player_name = item.player_name
        if not player_name:
            # Do not invent a player attachment when matching was uncertain.
            player_name = "Unknown"
        injuries.append(
            InjuryUpdate(
                injury_id=f"injury_{stable_hash(item.news_id, player_name)}",
                player_id=item.player_id,
                player_name=player_name,
                team=item.team,
                injury_status=_status(summary_text),
                body_part=_body_part(summary_text),
                report_text_summary=summary_text,
                source_name=item.source_name,
                source_url=item.source_url,
                reported_at=item.published_at,
            )
        )
    return injuries

