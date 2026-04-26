"""Top-level update orchestration."""

from __future__ import annotations

import logging

from cfb_intel.pipeline.collect_injuries import extract_injuries
from cfb_intel.pipeline.collect_news import collect_news
from cfb_intel.pipeline.collect_rosters import collect_rosters
from cfb_intel.pipeline.dedupe import dedupe_players
from cfb_intel.pipeline.export import export_all
from cfb_intel.pipeline.normalize import normalize_players
from cfb_intel.schemas import InjuryUpdate, NewsItem, Player, Team

LOGGER = logging.getLogger(__name__)


def run_update(*, rosters: bool = True, news: bool = True, injuries: bool = True) -> dict[str, int]:
    roster_result = collect_rosters() if rosters else {"players": [], "teams": []}
    players = dedupe_players(normalize_players(list(roster_result.get("players", []))))
    teams: list[Team] = list(roster_result.get("teams", []))

    news_items: list[NewsItem] = collect_news(players, teams).get("news", []) if news else []
    injury_items: list[InjuryUpdate] = extract_injuries(news_items) if injuries else []

    export_all(players, teams, news_items, injury_items)
    summary = {
        "players": len(players),
        "teams": len(teams),
        "stats_rows": 0,
        "news_items": len(news_items),
        "injury_items": len(injury_items),
    }
    LOGGER.info("update complete", extra={f"cfb_{key}": value for key, value in summary.items()})
    return summary
