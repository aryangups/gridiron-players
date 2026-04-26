"""Pydantic data contracts for normalized exports."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from enum import StrEnum
from typing import Literal

from pydantic import BaseModel, Field, HttpUrl, validator


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class PlayerStatus(StrEnum):
    active = "active"
    injured = "injured"
    transferred = "transferred"
    graduated = "graduated"
    unknown = "unknown"


class InjuryStatus(StrEnum):
    questionable = "questionable"
    probable = "probable"
    doubtful = "doubtful"
    out = "out"
    season_ending = "season-ending"
    day_to_day = "day-to-day"
    unknown = "unknown"


NewsTag = Literal[
    "injury",
    "transfer",
    "depth_chart",
    "performance",
    "award",
    "recruiting",
    "discipline",
    "draft",
    "general",
]


class ExportModel(BaseModel):
    class Config:
        extra = "forbid"
        use_enum_values = True
        json_encoders = {datetime: lambda value: value.isoformat()}

    def model_dump(self, *args, **kwargs):
        kwargs.pop("mode", None)
        return json.loads(self.json())

    def model_copy(self, *, update=None):
        return self.copy(update=update or {})


class Player(ExportModel):
    player_id: str
    full_name: str
    first_name: str | None = None
    last_name: str | None = None
    team: str
    team_id: str | None = None
    conference: str | None = None
    position: str | None = None
    jersey_number: str | None = None
    height: str | None = None
    weight: str | None = None
    class_year: str | None = None
    hometown: str | None = None
    high_school: str | None = None
    previous_school: str | None = None
    birth_date: str | None = None
    recruiting_stars: int | None = Field(default=None, ge=1, le=5)
    status: PlayerStatus = PlayerStatus.unknown
    source_urls: list[HttpUrl] = Field(default_factory=list)
    last_updated: datetime = Field(default_factory=utc_now)

    @validator("full_name", "team")
    @classmethod
    def required_text(cls, value: str) -> str:
        cleaned = " ".join(value.split())
        if not cleaned:
            raise ValueError("value cannot be blank")
        return cleaned


class PlayerStats(ExportModel):
    player_id: str
    season: int
    team: str
    games_played: int | None = None
    games_started: int | None = None
    position_group: str | None = None
    completions: int | None = None
    attempts: int | None = None
    passing_yards: int | None = None
    passing_tds: int | None = None
    interceptions: int | None = None
    passer_rating: float | None = None
    carries: int | None = None
    rushing_yards: int | None = None
    rushing_tds: int | None = None
    yards_per_carry: float | None = None
    receptions: int | None = None
    receiving_yards: int | None = None
    receiving_tds: int | None = None
    yards_per_reception: float | None = None
    tackles: int | None = None
    solo_tackles: int | None = None
    sacks: float | None = None
    tackles_for_loss: float | None = None
    forced_fumbles: int | None = None
    pass_breakups: int | None = None
    field_goals_made: int | None = None
    field_goals_attempted: int | None = None
    extra_points_made: int | None = None
    extra_points_attempted: int | None = None
    punts: int | None = None
    punt_yards: int | None = None
    average_punt: float | None = None
    source_url: HttpUrl
    last_updated: datetime = Field(default_factory=utc_now)


class NewsItem(ExportModel):
    news_id: str
    player_id: str | None = None
    player_name: str | None = None
    team: str | None = None
    headline: str
    source_name: str
    source_url: HttpUrl
    published_at: datetime
    summary: str | None = None
    tags: list[NewsTag] = Field(default_factory=lambda: ["general"])
    confidence_score: float = Field(default=0.0, ge=0.0, le=1.0)
    last_updated: datetime = Field(default_factory=utc_now)


class InjuryUpdate(ExportModel):
    injury_id: str
    player_id: str | None = None
    player_name: str
    team: str | None = None
    injury_status: InjuryStatus = InjuryStatus.unknown
    body_part: str | None = None
    report_text_summary: str
    source_name: str
    source_url: HttpUrl
    reported_at: datetime
    last_updated: datetime = Field(default_factory=utc_now)


class Team(ExportModel):
    team_id: str
    team_name: str
    abbreviation: str | None = None
    conference: str | None = None
    division: str | None = None
    official_site: HttpUrl | None = None
    roster_url: HttpUrl | None = None
    source_urls: list[HttpUrl] = Field(default_factory=list)
    last_updated: datetime = Field(default_factory=utc_now)
