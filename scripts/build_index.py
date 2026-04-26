"""Rebuild the player search index from current exports."""

from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from cfb_intel.config import EXPORT_DIR
from cfb_intel.pipeline.export import build_player_index
from cfb_intel.schemas import InjuryUpdate, NewsItem, Player


def _load(path: Path, model):
    if not path.exists():
        return []
    return [model(**row) for row in json.loads(path.read_text(encoding="utf-8"))]


def main() -> int:
    index = build_player_index(
        _load(EXPORT_DIR / "players.json", Player),
        _load(EXPORT_DIR / "news.json", NewsItem),
        _load(EXPORT_DIR / "injuries.json", InjuryUpdate),
    )
    (EXPORT_DIR / "player_index.json").write_text(json.dumps(index, indent=2), encoding="utf-8")
    print(f"Indexed {len(index['players'])} players")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

