"""Run one or more CFB intelligence pipeline stages."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from cfb_intel.pipeline.update_all import run_update
from cfb_intel.utils.logging import configure_logging


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--all", action="store_true", help="Run all MVP stages")
    parser.add_argument("--rosters", action="store_true", help="Collect rosters")
    parser.add_argument("--stats", action="store_true", help="Reserved for stats sources")
    parser.add_argument("--news", action="store_true", help="Collect news metadata")
    parser.add_argument("--injuries", action="store_true", help="Extract injury updates from news")
    return parser.parse_args()


def main() -> int:
    configure_logging()
    args = parse_args()
    if args.all or not any([args.rosters, args.stats, args.news, args.injuries]):
        summary = run_update(rosters=True, news=True, injuries=True)
    else:
        run_rosters = args.rosters or args.news or args.injuries
        summary = run_update(rosters=run_rosters, news=args.news or args.injuries, injuries=args.injuries)
    print(summary)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

