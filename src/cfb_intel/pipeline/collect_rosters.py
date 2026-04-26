"""Roster collection stage."""

from __future__ import annotations

from cfb_intel.sources import get_sources


def collect_rosters() -> dict[str, list[object]]:
    output: dict[str, list[object]] = {"players": [], "teams": []}
    for source in get_sources("rosters"):
        result = source.run()
        output["players"].extend(result.get("players", []))
        output["teams"].extend(result.get("teams", []))
    return output

