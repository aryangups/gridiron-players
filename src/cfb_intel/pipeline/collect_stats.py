"""Historical player stats collection from public ESPN athlete endpoints."""

from __future__ import annotations

import json
import logging
from collections import defaultdict
from typing import Any

from cfb_intel.config import settings
from cfb_intel.schemas import Player, PlayerStats
from cfb_intel.utils.http import PoliteHttpClient

LOGGER = logging.getLogger(__name__)

STATS_BASE = "https://site.web.api.espn.com/apis/common/v3/sports/football/college-football/athletes"

FIELD_MAP = {
    "completions": "completions",
    "passingAttempts": "attempts",
    "passingYards": "passing_yards",
    "passingTouchdowns": "passing_tds",
    "interceptions": "interceptions",
    "QBRating": "passer_rating",
    "rushingAttempts": "carries",
    "rushingYards": "rushing_yards",
    "rushingTouchdowns": "rushing_tds",
    "yardsPerRushAttempt": "yards_per_carry",
    "receptions": "receptions",
    "receivingYards": "receiving_yards",
    "receivingTouchdowns": "receiving_tds",
    "yardsPerReception": "yards_per_reception",
    "totalTackles": "tackles",
    "soloTackles": "solo_tackles",
    "sacks": "sacks",
    "tacklesForLoss": "tackles_for_loss",
    "forcedFumbles": "forced_fumbles",
    "passesDefended": "pass_breakups",
    "fieldGoalsMade": "field_goals_made",
    "fieldGoalAttempts": "field_goals_attempted",
    "kickExtraPoints": "extra_points_made",
    "kickExtraPointAttempts": "extra_points_attempted",
    "punts": "punts",
    "puntYards": "punt_yards",
    "grossAvgPuntYards": "average_punt",
}

INT_FIELDS = {
    "completions",
    "attempts",
    "passing_yards",
    "passing_tds",
    "interceptions",
    "carries",
    "rushing_yards",
    "rushing_tds",
    "receptions",
    "receiving_yards",
    "receiving_tds",
    "tackles",
    "solo_tackles",
    "forced_fumbles",
    "pass_breakups",
    "field_goals_made",
    "field_goals_attempted",
    "extra_points_made",
    "extra_points_attempted",
    "punts",
    "punt_yards",
}


def _espn_athlete_id(player: Player) -> str | None:
    if player.player_id.startswith("espn_"):
        return player.player_id.removeprefix("espn_")
    for url in player.source_urls:
        text = str(url)
        marker = "/id/"
        if marker in text:
            return text.split(marker, 1)[1].split("/", 1)[0]
    return None


def _number(value: str, field_name: str) -> int | float | None:
    cleaned = str(value).replace(",", "").strip()
    if cleaned in {"", "--", "-"}:
        return None
    try:
        number = float(cleaned)
    except ValueError:
        return None
    if field_name in INT_FIELDS:
        return int(number)
    return number


def _team_name(payload: dict[str, Any], team_id: str | None, fallback: str) -> str:
    if not team_id:
        return fallback
    for team in payload.get("teams", {}).values():
        if str(team.get("id")) == str(team_id):
            return team.get("displayName") or fallback
    return fallback


def _rows_from_payload(player: Player, athlete_id: str, payload: dict[str, Any]) -> list[PlayerStats]:
    source_url = f"{STATS_BASE}/{athlete_id}/stats"
    grouped: dict[tuple[int, str], dict[str, Any]] = defaultdict(
        lambda: {
            "player_id": player.player_id,
            "season": 0,
            "team": player.team,
            "position_group": player.position,
            "source_url": source_url,
        }
    )

    for category in payload.get("categories", []):
        names = category.get("names") or []
        for stat_row in category.get("statistics", []):
            season = int((stat_row.get("season") or {}).get("year") or 0)
            if not season:
                continue
            team = _team_name(payload, stat_row.get("teamId"), player.team)
            key = (season, team)
            grouped[key]["season"] = season
            grouped[key]["team"] = team
            grouped[key]["position_group"] = stat_row.get("position") or grouped[key].get("position_group")
            for raw_name, raw_value in zip(names, stat_row.get("stats") or [], strict=False):
                target = FIELD_MAP.get(raw_name)
                if not target:
                    continue
                value = _number(raw_value, target)
                if value is not None:
                    grouped[key][target] = value

    rows: list[PlayerStats] = []
    for row in grouped.values():
        try:
            rows.append(PlayerStats(**row))
        except Exception as exc:
            LOGGER.warning("player stats row skipped", extra={"cfb_player_id": player.player_id, "cfb_error": str(exc)})
    return rows


def collect_stats(players: list[Player]) -> dict[str, list[PlayerStats]]:
    if not settings.enable_player_stats:
        return {"stats": []}

    selected = players[: settings.max_stats_players] if settings.max_stats_players > 0 else players
    client = PoliteHttpClient(delay_seconds=settings.stats_request_delay_seconds)
    stats: list[PlayerStats] = []
    for index, player in enumerate(selected, start=1):
        athlete_id = _espn_athlete_id(player)
        if not athlete_id:
            continue
        url = f"{STATS_BASE}/{athlete_id}/stats"
        result = client.get(url)
        if not result or result.status_code != 200:
            continue
        try:
            payload = json.loads(result.text)
        except json.JSONDecodeError:
            continue
        stats.extend(_rows_from_payload(player, athlete_id, payload))
        if index % 500 == 0:
            LOGGER.info("player stats progress", extra={"cfb_players_checked": index, "cfb_stats_rows": len(stats)})
    return {"stats": stats}

