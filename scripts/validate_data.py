"""Validate generated export files."""

from __future__ import annotations

import json
import sqlite3
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EXPORTS = ROOT / "data" / "exports"
REQUIRED = [
    "players.json",
    "players.csv",
    "teams.json",
    "news.json",
    "injuries.json",
    "player_index.json",
    "cfb_intel.sqlite",
]


def _load_json(name: str):
    path = EXPORTS / name
    if not path.exists():
        raise AssertionError(f"missing {name}")
    return json.loads(path.read_text(encoding="utf-8"))


def main() -> int:
    for name in REQUIRED:
        if not (EXPORTS / name).exists():
            raise AssertionError(f"missing export file: {name}")
    players = _load_json("players.json")
    news = _load_json("news.json")
    _load_json("teams.json")
    _load_json("injuries.json")
    index = _load_json("player_index.json")

    seen: set[str] = set()
    for player in players:
        for key in ["player_id", "full_name", "team", "last_updated"]:
            if not player.get(key):
                raise AssertionError(f"player missing {key}: {player}")
        if not player.get("source_urls"):
            raise AssertionError(f"player missing source_urls: {player['player_id']}")
        if player["player_id"] in seen:
            raise AssertionError(f"duplicate player_id: {player['player_id']}")
        seen.add(player["player_id"])

    for item in news:
        for key in ["headline", "source_url", "source_name", "published_at"]:
            if not item.get(key):
                raise AssertionError(f"news missing {key}: {item}")

    with sqlite3.connect(EXPORTS / "cfb_intel.sqlite") as conn:
        conn.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()

    print(
        json.dumps(
            {
                "players": len(players),
                "news": len(news),
                "indexed_players": len(index.get("players", [])),
                "status": "ok",
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

