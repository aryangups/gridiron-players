"""Source registry."""

from __future__ import annotations

from cfb_intel.config import settings
from cfb_intel.sources.base import Source
from cfb_intel.sources.rss_news import GoogleNewsRssSource
from cfb_intel.sources.team_sites import TeamSeedRosterSource


def get_sources(kind: str | None = None) -> list[Source]:
    sources: list[Source] = [TeamSeedRosterSource()]
    if settings.enable_google_news_rss:
        sources.append(GoogleNewsRssSource())
    if kind:
        return [source for source in sources if source.kind == kind]
    return sources

