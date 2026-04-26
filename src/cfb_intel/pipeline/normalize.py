"""Normalization helpers."""

from __future__ import annotations

from cfb_intel.schemas import Player
from cfb_intel.utils.text import split_name


def normalize_players(players: list[Player]) -> list[Player]:
    normalized: list[Player] = []
    for player in players:
        first, last = split_name(player.full_name)
        normalized.append(player.model_copy(update={"first_name": player.first_name or first, "last_name": player.last_name or last}))
    return normalized

