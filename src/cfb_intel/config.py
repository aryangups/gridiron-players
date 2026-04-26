"""Runtime configuration for the CFB intelligence pipeline."""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path

try:
    from dotenv import load_dotenv

    load_dotenv()
except Exception:
    pass


ROOT_DIR = Path(__file__).resolve().parents[2]
DATA_DIR = ROOT_DIR / "data"
RAW_DIR = DATA_DIR / "raw"
PROCESSED_DIR = DATA_DIR / "processed"
EXPORT_DIR = DATA_DIR / "exports"
LOG_DIR = ROOT_DIR / "logs"


def _bool(name: str, default: bool) -> bool:
    return os.getenv(name, str(default)).strip().lower() in {"1", "true", "yes", "on"}


def _int(name: str, default: int) -> int:
    try:
        return int(os.getenv(name, str(default)))
    except ValueError:
        return default


def _float(name: str, default: float) -> float:
    try:
        return float(os.getenv(name, str(default)))
    except ValueError:
        return default


@dataclass(frozen=True)
class TeamSeed:
    team_id: str
    team_name: str
    abbreviation: str
    conference: str
    official_site: str
    roster_url: str


MVP_TEAMS: list[TeamSeed] = [
    TeamSeed("alabama", "Alabama", "ALA", "SEC", "https://rolltide.com", "https://rolltide.com/sports/football/roster"),
    TeamSeed("georgia", "Georgia", "UGA", "SEC", "https://georgiadogs.com", "https://georgiadogs.com/sports/football/roster"),
    TeamSeed("ohio-state", "Ohio State", "OSU", "Big Ten", "https://ohiostatebuckeyes.com", "https://ohiostatebuckeyes.com/sports/football/roster"),
    TeamSeed("michigan", "Michigan", "MICH", "Big Ten", "https://mgoblue.com", "https://mgoblue.com/sports/football/roster"),
    TeamSeed("texas", "Texas", "TEX", "SEC", "https://texassports.com", "https://texassports.com/sports/football/roster"),
]


@dataclass(frozen=True)
class Settings:
    enable_espn: bool = _bool("ENABLE_ESPN", False)
    enable_sports_reference: bool = _bool("ENABLE_SPORTS_REFERENCE", False)
    enable_ncaa: bool = _bool("ENABLE_NCAA", False)
    enable_google_news_rss: bool = _bool("ENABLE_GOOGLE_NEWS_RSS", True)
    enable_team_rss: bool = _bool("ENABLE_TEAM_RSS", True)
    request_delay_seconds: float = _float("REQUEST_DELAY_SECONDS", 2.0)
    max_news_per_player: int = _int("MAX_NEWS_PER_PLAYER", 10)
    max_teams_initial_run: int = _int("MAX_TEAMS_INITIAL_RUN", 10)
    full_run: bool = _bool("FULL_RUN", False)
    demo_mode: bool = _bool("DEMO_MODE", False)
    contact_email: str = os.getenv("CFB_INTEL_CONTACT_EMAIL", "example@example.com")
    teams: list[TeamSeed] = field(default_factory=lambda: MVP_TEAMS)

    @property
    def active_teams(self) -> list[TeamSeed]:
        if self.full_run:
            return self.teams
        return self.teams[: self.max_teams_initial_run]

    @property
    def user_agent(self) -> str:
        return f"CollegeFootballIntelBot/0.1 contact: {self.contact_email}"


settings = Settings()

