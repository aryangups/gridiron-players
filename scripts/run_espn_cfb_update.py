"""Run ESPN college football scoreboard and player game-stat collection."""

from __future__ import annotations

import argparse
import json
import sys
from datetime import date, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from cfb_intel.config import settings  # noqa: E402
from cfb_intel.pipeline.espn_cfb_live import polling_dates, run_espn_cfb_update  # noqa: E402
from cfb_intel.utils.logging import configure_logging  # noqa: E402


def _date(value: str) -> date:
    return datetime.strptime(value, "%Y-%m-%d").date()


def _weeks(value: str | None) -> list[int] | None:
    if not value:
        return None
    if value == "regular":
        return list(range(1, 17))
    if value == "postseason":
        return [1, 999]
    if value == "all":
        return list(range(1, 17))
    return [int(part.strip()) for part in value.split(",") if part.strip()]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--date", action="append", type=_date, help="YYYY-MM-DD scoreboard date. Can be repeated.")
    parser.add_argument("--season", type=int, default=settings.espn_season)
    parser.add_argument("--season-type", type=int, default=2, help="ESPN season type: 2 regular season, 3 postseason.")
    parser.add_argument(
        "--weeks",
        help="Comma-separated weeks, or regular/postseason/all. If omitted, polls current date window.",
    )
    parser.add_argument("--use-cache", action="store_true", help="Use local HTTP cache for historical backfills.")
    args = parser.parse_args()

    configure_logging()
    week_list = _weeks(args.weeks)
    dates = args.date if args.date else None
    if not week_list and not dates:
        dates = polling_dates()
    summary = run_espn_cfb_update(
        target_dates=dates,
        season=args.season,
        season_type=args.season_type,
        weeks=week_list,
        use_cache=args.use_cache,
    )
    print(json.dumps(summary, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
