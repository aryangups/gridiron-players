"""Player identity and deduplication."""

from __future__ import annotations

import json

from cfb_intel.config import PROCESSED_DIR
from cfb_intel.schemas import Player
from cfb_intel.utils.text import normalize_name, stable_hash


def player_identity_key(player: Player) -> str:
    return "|".join(
        [
            normalize_name(player.full_name),
            normalize_name(player.team),
            normalize_name(player.position or ""),
            normalize_name(player.jersey_number or ""),
            normalize_name(player.class_year or ""),
            normalize_name(player.hometown or ""),
        ]
    )


def dedupe_players(players: list[Player]) -> list[Player]:
    seen: dict[str, Player] = {}
    id_map: dict[str, str] = {}
    for player in players:
        key = player_identity_key(player)
        if key in seen:
            existing = seen[key]
            urls = sorted({str(url) for url in existing.source_urls + player.source_urls})
            seen[key] = existing.model_copy(update={"source_urls": urls})
            continue
        stable_id = player.player_id or f"cfb_{stable_hash(key)}"
        seen[key] = player.model_copy(update={"player_id": stable_id})
        id_map[key] = stable_id
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    (PROCESSED_DIR / "player_id_map.json").write_text(json.dumps(id_map, indent=2), encoding="utf-8")
    return list(seen.values())

