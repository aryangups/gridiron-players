"""ESPN college football scoreboard and player box-score collection."""

from __future__ import annotations

import json
import logging
from collections import defaultdict
from datetime import date, timedelta
from pathlib import Path
from typing import Any

from pydantic import BaseModel

from cfb_intel.config import EXPORT_DIR, settings
from cfb_intel.schemas import EspnCfbGame, EspnCfbPlayerGameStat, Player
from cfb_intel.storage.sqlite_store import write_sqlite
from cfb_intel.utils.http import PoliteHttpClient
from cfb_intel.utils.text import stable_hash

LOGGER = logging.getLogger(__name__)

SITE_BASE = "https://site.api.espn.com/apis/site/v2/sports/football/college-football"


def _dump_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")


def _model_rows(records: list[BaseModel]) -> list[dict[str, Any]]:
    return [record.model_dump(mode="json") for record in records]


def _int(value: Any) -> int | None:
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _float(value: Any) -> float | None:
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _stat_value(value: Any) -> int | float | str | None:
    text = str(value).replace(",", "").strip()
    if text in {"", "-", "--", "---"}:
        return None
    if "/" in text:
        return text
    try:
        number = float(text)
    except ValueError:
        return str(value)
    return int(number) if number.is_integer() else number


def _clean_key(key: str) -> str:
    return key.replace(".", "_").replace("-", "_").replace("/", "_")


def _json(client: PoliteHttpClient, url: str, *, use_cache: bool) -> dict[str, Any]:
    result = client.get(url, use_cache=use_cache)
    if not result or result.status_code != 200:
        return {}
    try:
        return json.loads(result.text)
    except json.JSONDecodeError:
        LOGGER.warning("ESPN CFB JSON decode failed", extra={"cfb_url": url})
        return {}


def _scoreboard_url_for_date(target_date: date) -> str:
    return (
        f"{SITE_BASE}/scoreboard?dates={target_date:%Y%m%d}"
        f"&groups={settings.espn_fbs_group_id}&limit=1000"
    )


def _scoreboard_url_for_week(season: int, season_type: int, week: int) -> str:
    return (
        f"{SITE_BASE}/scoreboard?dates={season}&seasontype={season_type}&week={week}"
        f"&groups={settings.espn_fbs_group_id}&limit=1000"
    )


def _summary_url(game_id: str) -> str:
    return f"{SITE_BASE}/summary?event={game_id}"


def _competitors(event: dict[str, Any]) -> dict[str, dict[str, Any]]:
    competition = (event.get("competitions") or [{}])[0]
    return {row.get("homeAway", ""): row for row in competition.get("competitors", [])}


def _game_from_event(event: dict[str, Any]) -> EspnCfbGame | None:
    try:
        competition = (event.get("competitions") or [{}])[0]
        status = competition.get("status") or event.get("status") or {}
        status_type = status.get("type") or {}
        competitors = _competitors(event)
        home = competitors.get("home") or {}
        away = competitors.get("away") or {}
        home_team = home.get("team") or {}
        away_team = away.get("team") or {}
        venue = competition.get("venue") or {}
        season = event.get("season") or {}
        return EspnCfbGame(
            game_id=str(event["id"]),
            season=int(season.get("year") or settings.espn_season),
            season_type=_int(season.get("type")),
            week=_int((event.get("week") or {}).get("number")),
            game_date=event["date"],
            name=event.get("name") or event.get("shortName") or str(event["id"]),
            short_name=event.get("shortName"),
            status=status_type.get("description") or status_type.get("name") or "unknown",
            status_detail=status_type.get("detail"),
            status_state=status_type.get("state"),
            completed=bool(status_type.get("completed", False)),
            period=_int(status.get("period")),
            clock=_float(status.get("clock")),
            home_team_id=str(home_team.get("id")) if home_team.get("id") else None,
            home_team=home_team.get("displayName"),
            home_score=_int(home.get("score")),
            away_team_id=str(away_team.get("id")) if away_team.get("id") else None,
            away_team=away_team.get("displayName"),
            away_score=_int(away.get("score")),
            venue=venue.get("fullName"),
            source_url=_summary_url(str(event["id"])),
        )
    except Exception as exc:
        LOGGER.warning("ESPN CFB game skipped", extra={"cfb_error": str(exc), "cfb_event": event.get("id")})
        return None


def collect_scoreboard_games(
    *,
    target_dates: list[date] | None = None,
    season: int | None = None,
    season_type: int = 2,
    weeks: list[int] | None = None,
    use_cache: bool = False,
) -> list[EspnCfbGame]:
    client = PoliteHttpClient(delay_seconds=settings.stats_request_delay_seconds)
    urls: list[str] = []
    if weeks:
        year = season or settings.espn_season
        urls.extend(_scoreboard_url_for_week(year, season_type, week) for week in weeks)
    else:
        dates = target_dates or [date.today()]
        urls.extend(_scoreboard_url_for_date(target_date) for target_date in dates)

    by_id: dict[str, EspnCfbGame] = {}
    for url in urls:
        payload = _json(client, url, use_cache=use_cache)
        for event in payload.get("events", []):
            game = _game_from_event(event)
            if game:
                by_id[game.game_id] = game
    games = list(by_id.values())
    if settings.espn_cfb_max_games > 0:
        games = games[: settings.espn_cfb_max_games]
    return games


def _side_and_opponent(summary: dict[str, Any], team_id: str) -> tuple[str | None, str | None]:
    competitors = summary.get("header", {}).get("competitions", [{}])[0].get("competitors", [])
    side = None
    opponent = None
    for row in competitors:
        team = row.get("team") or {}
        if str(team.get("id")) == str(team_id):
            side = row.get("homeAway")
        else:
            opponent = team.get("displayName")
    return side, opponent


def collect_player_game_stats(games: list[EspnCfbGame], *, use_cache: bool = False) -> list[EspnCfbPlayerGameStat]:
    client = PoliteHttpClient(delay_seconds=settings.stats_request_delay_seconds)
    rows: list[EspnCfbPlayerGameStat] = []
    for index, game in enumerate(games, start=1):
        payload = _json(client, str(game.source_url), use_cache=use_cache)
        if not payload:
            continue
        for team_group in (payload.get("boxscore") or {}).get("players", []):
            team = team_group.get("team") or {}
            team_id = str(team.get("id") or "")
            if not team_id:
                continue
            side, opponent = _side_and_opponent(payload, team_id)
            for stat_group in team_group.get("statistics", []):
                stat_type = stat_group.get("name") or stat_group.get("type") or "unknown"
                keys = [_clean_key(key) for key in stat_group.get("keys") or []]
                for athlete_row in stat_group.get("athletes", []):
                    athlete = athlete_row.get("athlete") or {}
                    athlete_id = str(athlete.get("id") or "")
                    if not athlete_id:
                        continue
                    stats = {
                        key: _stat_value(value)
                        for key, value in zip(keys, athlete_row.get("stats") or [], strict=False)
                    }
                    rows.append(
                        EspnCfbPlayerGameStat(
                            stat_id="espn_cfb_game_stat_"
                            + stable_hash(game.game_id, athlete_id, str(stat_type), team_id),
                            game_id=game.game_id,
                            season=game.season,
                            season_type=game.season_type,
                            week=game.week,
                            game_date=game.game_date,
                            player_id=f"espn_{athlete_id}",
                            espn_athlete_id=athlete_id,
                            player_name=athlete.get("displayName") or "Unknown",
                            team_id=f"espn_{team_id}",
                            team=team.get("displayName") or "Unknown",
                            opponent=opponent,
                            home_away=side,
                            jersey=athlete.get("jersey"),
                            stat_type=str(stat_type),
                            stats=stats,
                            source_url=game.source_url,
                        )
                    )
        if index % 50 == 0:
            LOGGER.info("ESPN CFB summaries processed", extra={"cfb_games": index, "cfb_stat_rows": len(rows)})
    return rows


def aggregate_player_season_totals(rows: list[EspnCfbPlayerGameStat]) -> list[dict[str, Any]]:
    totals: dict[tuple[str, int, str], dict[str, Any]] = {}
    names: dict[str, str] = {}
    for row in rows:
        key = (row.player_id, row.season, row.stat_type)
        target = totals.setdefault(
            key,
            {
                "player_id": row.player_id,
                "espn_athlete_id": row.espn_athlete_id,
                "player_name": row.player_name,
                "season": row.season,
                "team": row.team,
                "stat_type": row.stat_type,
                "games_with_stat": 0,
                "stats": {},
                "source_urls": set(),
            },
        )
        names[row.player_id] = row.player_name
        target["games_with_stat"] += 1
        target["source_urls"].add(str(row.source_url))
        for stat_name, value in row.stats.items():
            if isinstance(value, (int, float)):
                target["stats"][stat_name] = target["stats"].get(stat_name, 0) + value
    output = []
    for item in totals.values():
        item["source_urls"] = sorted(item["source_urls"])
        output.append(item)
    return sorted(output, key=lambda item: (item["player_name"], item["season"], item["stat_type"]))


def _load_players(path: Path) -> list[Player]:
    if not path.exists():
        return []
    return [Player(**row) for row in json.loads(path.read_text(encoding="utf-8"))]


def attach_game_stats_to_players(players: list[Player], rows: list[EspnCfbPlayerGameStat], *, max_rows: int = 50) -> list[Player]:
    by_player: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in sorted(rows, key=lambda item: item.game_date, reverse=True):
        if len(by_player[row.player_id]) >= max_rows:
            continue
        by_player[row.player_id].append(row.model_dump(mode="json"))
    return [player.model_copy(update={"game_stats": by_player.get(player.player_id, player.game_stats)}) for player in players]


def export_espn_cfb(games: list[EspnCfbGame], rows: list[EspnCfbPlayerGameStat]) -> dict[str, int]:
    game_rows = _model_rows(games)
    stat_rows = _model_rows(rows)
    totals = aggregate_player_season_totals(rows)
    active_states = {"in", "pre"}
    scoreboard = {
        "games": game_rows,
        "summary": {
            "game_count": len(games),
            "active_or_upcoming_game_count": sum(1 for game in games if (game.status_state or "").lower() in active_states),
            "player_game_stat_count": len(rows),
            "season_total_count": len(totals),
        },
    }
    _dump_json(EXPORT_DIR / "espn_cfb_games.json", game_rows)
    _dump_json(EXPORT_DIR / "espn_cfb_player_game_stats.json", stat_rows)
    _dump_json(EXPORT_DIR / "espn_cfb_player_season_totals.json", totals)
    _dump_json(EXPORT_DIR / "espn_cfb_scoreboard.json", scoreboard)

    players_path = EXPORT_DIR / "players.json"
    players = _load_players(players_path)
    if players:
        updated_players = attach_game_stats_to_players(players, rows)
        _dump_json(players_path, _model_rows(updated_players))

    write_sqlite(
        EXPORT_DIR / "espn_cfb.sqlite",
        games=games,
        player_game_stats=rows,
    )
    return {
        "games": len(games),
        "player_game_stats": len(rows),
        "player_season_totals": len(totals),
    }


def run_espn_cfb_update(
    *,
    target_dates: list[date] | None = None,
    season: int | None = None,
    season_type: int = 2,
    weeks: list[int] | None = None,
    use_cache: bool = False,
) -> dict[str, int]:
    games = collect_scoreboard_games(
        target_dates=target_dates,
        season=season,
        season_type=season_type,
        weeks=weeks,
        use_cache=use_cache,
    )
    stats = collect_player_game_stats(games, use_cache=use_cache)
    return export_espn_cfb(games, stats)


def polling_dates(today: date | None = None) -> list[date]:
    anchor = today or date.today()
    start = anchor - timedelta(days=settings.espn_cfb_poll_lookback_days)
    end = anchor + timedelta(days=settings.espn_cfb_poll_lookahead_days)
    days = (end - start).days + 1
    return [start + timedelta(days=offset) for offset in range(days)]
