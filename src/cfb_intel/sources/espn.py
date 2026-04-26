"""ESPN public endpoint roster adapter.

This source uses public JSON endpoints that power ESPN's college football site.
They are not a guaranteed, contracted API, so the adapter is isolated and can be
disabled with ENABLE_ESPN=false. It stores ESPN profile/roster URLs as source
links and skips failures per team instead of failing the full run.
"""

from __future__ import annotations

import json
import logging
import re
from typing import Any

from cfb_intel.config import settings
from cfb_intel.schemas import Player, Team
from cfb_intel.sources.base import Source
from cfb_intel.utils.http import PoliteHttpClient
from cfb_intel.utils.text import stable_hash

LOGGER = logging.getLogger(__name__)

CORE_BASE = "https://sports.core.api.espn.com/v2/sports/football/leagues/college-football"
SITE_BASE = "https://site.api.espn.com/apis/site/v2/sports/football/college-football"


def _https(url: str) -> str:
    return url.replace("http://", "https://", 1)


def _json_from_result(result: Any) -> dict[str, Any] | None:
    if not result or result.status_code != 200:
        return None
    try:
        return json.loads(result.text)
    except json.JSONDecodeError:
        return None


def _link_with_rel(links: list[dict[str, Any]] | None, rel_name: str) -> str | None:
    for link in links or []:
        if rel_name in link.get("rel", []):
            return link.get("href")
    return None


def _team_id_from_ref(ref: str) -> str:
    match = re.search(r"/teams/(\d+)", ref)
    return match.group(1) if match else stable_hash(ref, length=8)


class EspnFbsRosterSource(Source):
    source_name = "ESPN public FBS roster endpoints"
    source_url = "https://site.api.espn.com/apis/site/v2/sports/football/college-football"
    kind = "rosters"
    enabled = settings.enable_espn

    def __init__(self) -> None:
        self.client = PoliteHttpClient(delay_seconds=settings.request_delay_seconds)

    def fetch(self) -> dict[str, Any]:
        season = settings.espn_season
        group_id = settings.espn_fbs_group_id
        fbs_url = (
            f"{CORE_BASE}/seasons/{season}/types/1/groups/{group_id}/teams"
            "?lang=en&region=us&limit=300"
        )
        group_result = self.client.get(fbs_url)
        group_payload = _json_from_result(group_result) or {"items": []}
        team_refs = [_https(item["$ref"]) for item in group_payload.get("items", []) if item.get("$ref")]
        if not settings.full_run:
            team_refs = team_refs[: settings.max_teams_initial_run]

        teams: list[dict[str, Any]] = []
        rosters: list[dict[str, Any]] = []
        for ref in team_refs:
            team_payload = _json_from_result(self.client.get(ref))
            if not team_payload:
                LOGGER.warning("ESPN team payload skipped", extra={"cfb_url": ref})
                continue
            team_id = str(team_payload.get("id") or _team_id_from_ref(ref))
            roster_url = f"{SITE_BASE}/teams/{team_id}/roster"
            roster_payload = _json_from_result(self.client.get(roster_url))
            if not roster_payload:
                LOGGER.warning("ESPN roster skipped", extra={"cfb_team_id": team_id, "cfb_url": roster_url})
                continue
            teams.append(team_payload)
            rosters.append({"team": team_payload, "roster": roster_payload, "roster_url": roster_url})
        return {"teams": teams, "rosters": rosters, "fbs_url": fbs_url}

    def parse(self, raw: dict[str, Any]) -> dict[str, Any]:
        return raw

    def normalize(self, parsed: dict[str, Any]) -> dict[str, list[object]]:
        conference_by_ref: dict[str, str] = {}
        teams: list[Team] = []
        players: list[Player] = []

        for row in parsed.get("rosters", []):
            team_payload = row["team"]
            roster_payload = row["roster"]
            team_id = str(team_payload.get("id"))
            display_name = team_payload.get("displayName") or team_payload.get("location") or team_id
            conference = self._conference_name(team_payload, conference_by_ref)
            team_links = team_payload.get("links", [])
            roster_page = _link_with_rel(team_links, "roster") or row["roster_url"]

            teams.append(
                Team(
                    team_id=f"espn_{team_id}",
                    team_name=display_name,
                    abbreviation=team_payload.get("abbreviation"),
                    conference=conference,
                    official_site=None,
                    roster_url=roster_page,
                    source_urls=[row["roster_url"], roster_page] if roster_page != row["roster_url"] else [row["roster_url"]],
                )
            )

            for group in roster_payload.get("athletes", []):
                for athlete in group.get("items", []):
                    full_name = athlete.get("fullName") or athlete.get("displayName")
                    if not full_name:
                        continue
                    position = athlete.get("position") or {}
                    experience = athlete.get("experience") or {}
                    birth_place = athlete.get("birthPlace") or {}
                    player_url = _link_with_rel(athlete.get("links"), "athlete")
                    source_urls = [url for url in [player_url, roster_page, row["roster_url"]] if url]
                    injuries = athlete.get("injuries") or []
                    players.append(
                        Player(
                            player_id=f"espn_{athlete.get('id') or stable_hash(full_name, team_id)}",
                            full_name=full_name,
                            first_name=athlete.get("firstName"),
                            last_name=athlete.get("lastName"),
                            team=display_name,
                            team_id=f"espn_{team_id}",
                            conference=conference,
                            position=position.get("abbreviation") or position.get("displayName"),
                            jersey_number=athlete.get("jersey"),
                            height=athlete.get("displayHeight"),
                            weight=athlete.get("displayWeight"),
                            class_year=experience.get("displayValue"),
                            hometown=birth_place.get("displayText"),
                            status="injured" if injuries else "active",
                            source_urls=source_urls,
                        )
                    )
        return {"teams": teams, "players": players}

    def _conference_name(self, team_payload: dict[str, Any], cache: dict[str, str]) -> str | None:
        group_ref = (team_payload.get("groups") or {}).get("$ref")
        if not group_ref:
            return None
        group_ref = _https(group_ref)
        if group_ref not in cache:
            group_payload = _json_from_result(self.client.get(group_ref))
            cache[group_ref] = (group_payload or {}).get("shortName") or (group_payload or {}).get("name") or ""
        return cache[group_ref] or None
