"""Team roster source.

The MVP uses a small seed roster for five teams so the pipeline is runnable
without hammering team sites or depending on brittle roster markup. Each row
keeps the public official roster URL as provenance. Future implementations can
replace fetch/parse with site-specific adapters after reviewing robots.txt and
site terms.
"""

from __future__ import annotations

from cfb_intel.config import settings
from cfb_intel.schemas import Player, Team
from cfb_intel.sources.base import Source
from cfb_intel.utils.text import split_name, stable_hash


SEED_PLAYERS = {
    "Alabama": [
        {"full_name": "Jalen Milroe", "position": "QB", "class_year": "Senior"},
        {"full_name": "Ryan Williams", "position": "WR", "class_year": "Sophomore"},
    ],
    "Georgia": [
        {"full_name": "Gunner Stockton", "position": "QB", "class_year": "Junior"},
        {"full_name": "Malaki Starks", "position": "DB", "class_year": "Senior"},
    ],
    "Ohio State": [
        {"full_name": "Julian Sayin", "position": "QB", "class_year": "Sophomore"},
        {"full_name": "Jeremiah Smith", "position": "WR", "class_year": "Sophomore"},
    ],
    "Michigan": [
        {"full_name": "Bryce Underwood", "position": "QB", "class_year": "Freshman"},
        {"full_name": "Mason Graham", "position": "DL", "class_year": "Senior"},
    ],
    "Texas": [
        {"full_name": "Arch Manning", "position": "QB", "class_year": "Sophomore"},
        {"full_name": "Anthony Hill Jr.", "position": "LB", "class_year": "Junior"},
    ],
}


class TeamSeedRosterSource(Source):
    source_name = "MVP official-roster seed"
    source_url = "configured official team roster URLs"
    kind = "rosters"

    def fetch(self) -> list[dict[str, object]]:
        rows: list[dict[str, object]] = []
        for team in settings.active_teams:
            for player in SEED_PLAYERS.get(team.team_name, []):
                rows.append({"team": team, "player": player})
        return rows

    def parse(self, raw: list[dict[str, object]]) -> list[dict[str, object]]:
        return raw

    def normalize(self, parsed: list[dict[str, object]]) -> dict[str, list[object]]:
        teams: list[Team] = []
        players: list[Player] = []
        for team_seed in settings.active_teams:
            teams.append(
                Team(
                    team_id=team_seed.team_id,
                    team_name=team_seed.team_name,
                    abbreviation=team_seed.abbreviation,
                    conference=team_seed.conference,
                    official_site=team_seed.official_site,
                    roster_url=team_seed.roster_url,
                    source_urls=[team_seed.roster_url],
                )
            )
        for row in parsed:
            team_seed = row["team"]
            player_row = row["player"]
            full_name = str(player_row["full_name"])
            first, last = split_name(full_name)
            players.append(
                Player(
                    player_id=f"cfb_{stable_hash(full_name, team_seed.team_id, str(player_row.get('position', '')))}",
                    full_name=full_name,
                    first_name=first,
                    last_name=last,
                    team=team_seed.team_name,
                    team_id=team_seed.team_id,
                    conference=team_seed.conference,
                    position=player_row.get("position"),
                    class_year=player_row.get("class_year"),
                    status="active",
                    source_urls=[team_seed.roster_url],
                )
            )
        return {"teams": teams, "players": players}

