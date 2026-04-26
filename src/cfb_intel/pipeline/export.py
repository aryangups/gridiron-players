"""Export normalized datasets to JSON, CSV, index, and SQLite."""

from __future__ import annotations

import json
import csv
from pathlib import Path
from typing import Any

from pydantic import BaseModel

from cfb_intel.config import EXPORT_DIR
from cfb_intel.schemas import InjuryUpdate, NewsItem, Player, PlayerStats, Team
from cfb_intel.storage.sqlite_store import write_sqlite


def _dump_json(path: Path, records: list[BaseModel]) -> None:
    payload = [record.model_dump(mode="json") for record in records]
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")


def _dump_csv(path: Path, records: list[BaseModel]) -> None:
    rows = [record.model_dump(mode="json") for record in records]
    if not rows:
        path.write_text("", encoding="utf-8")
        return
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def build_player_index(players: list[Player], news: list[NewsItem], injuries: list[InjuryUpdate]) -> dict[str, list[dict[str, Any]]]:
    news_count: dict[str, int] = {}
    injury_status: dict[str, str] = {}
    for item in news:
        if item.player_id:
            news_count[item.player_id] = news_count.get(item.player_id, 0) + 1
    for injury in injuries:
        if injury.player_id:
            injury_status[injury.player_id] = injury.injury_status
    return {
        "players": [
            {
                "player_id": player.player_id,
                "name": player.full_name,
                "team": player.team,
                "position": player.position,
                "conference": player.conference,
                "latest_news_count": news_count.get(player.player_id, 0),
                "injury_status": injury_status.get(player.player_id, "unknown"),
                "last_updated": player.last_updated.isoformat(),
            }
            for player in players
        ]
    }


def export_all(
    players: list[Player],
    teams: list[Team],
    news: list[NewsItem],
    injuries: list[InjuryUpdate],
    stats: list[PlayerStats] | None = None,
) -> None:
    stats = stats or []
    EXPORT_DIR.mkdir(parents=True, exist_ok=True)
    _dump_json(EXPORT_DIR / "players.json", players)
    _dump_csv(EXPORT_DIR / "players.csv", players)
    _dump_json(EXPORT_DIR / "teams.json", teams)
    _dump_json(EXPORT_DIR / "player_stats.json", stats)
    _dump_json(EXPORT_DIR / "news.json", news)
    _dump_json(EXPORT_DIR / "injuries.json", injuries)
    index = build_player_index(players, news, injuries)
    (EXPORT_DIR / "player_index.json").write_text(json.dumps(index, indent=2), encoding="utf-8")
    write_sqlite(EXPORT_DIR / "cfb_intel.sqlite", players=players, teams=teams, stats=stats, news=news, injuries=injuries)
