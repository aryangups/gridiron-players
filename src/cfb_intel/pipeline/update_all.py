"""Top-level update orchestration."""

from __future__ import annotations

import logging
import json

from cfb_intel.config import EXPORT_DIR
from cfb_intel.pipeline.collect_injuries import extract_injuries
from cfb_intel.pipeline.collect_news import collect_news
from cfb_intel.pipeline.collect_rosters import collect_rosters
from cfb_intel.pipeline.collect_stats import collect_stats
from cfb_intel.pipeline.dedupe import dedupe_players
from cfb_intel.pipeline.export import export_all
from cfb_intel.pipeline.normalize import normalize_players
from cfb_intel.schemas import InjuryUpdate, NewsItem, PlayerStats, Team

LOGGER = logging.getLogger(__name__)


def _attach_stats(players, stats: list[PlayerStats]):
    by_player: dict[str, list[dict[str, object]]] = {}
    for row in stats:
        by_player.setdefault(row.player_id, []).append(row.model_dump(mode="json"))
    return [player.model_copy(update={"stats": by_player.get(player.player_id, [])}) for player in players]


def _load_existing(name: str, model):
    path = EXPORT_DIR / name
    if not path.exists():
        return []
    try:
        return [model(**row) for row in json.loads(path.read_text(encoding="utf-8"))]
    except Exception as exc:
        LOGGER.warning("existing export could not be loaded", extra={"cfb_file": name, "cfb_error": str(exc)})
        return []


def run_update(*, rosters: bool = True, stats: bool = True, news: bool = True, injuries: bool = True) -> dict[str, int]:
    roster_result = collect_rosters() if rosters else {"players": [], "teams": []}
    players = dedupe_players(normalize_players(list(roster_result.get("players", []))))
    teams: list[Team] = list(roster_result.get("teams", []))

    stats_rows: list[PlayerStats] = collect_stats(players).get("stats", []) if stats else _load_existing("player_stats.json", PlayerStats)
    players = _attach_stats(players, stats_rows)
    news_items: list[NewsItem] = collect_news(players, teams).get("news", []) if news else _load_existing("news.json", NewsItem)
    injury_items: list[InjuryUpdate] = extract_injuries(news_items) if injuries else _load_existing("injuries.json", InjuryUpdate)

    export_all(players, teams, news_items, injury_items, stats_rows)
    summary = {
        "players": len(players),
        "teams": len(teams),
        "stats_rows": len(stats_rows),
        "news_items": len(news_items),
        "injury_items": len(injury_items),
    }
    LOGGER.info("update complete", extra={f"cfb_{key}": value for key, value in summary.items()})
    return summary
