"""RSS news metadata source."""

from __future__ import annotations

import logging
from urllib.parse import quote_plus

import feedparser

from cfb_intel.config import settings
from cfb_intel.schemas import NewsItem
from cfb_intel.sources.base import Source
from cfb_intel.utils.dates import parse_datetime
from cfb_intel.utils.http import PoliteHttpClient
from cfb_intel.utils.text import classify_news, short_summary, stable_hash

LOGGER = logging.getLogger(__name__)


class GoogleNewsRssSource(Source):
    source_name = "Google News RSS"
    source_url = "https://news.google.com/rss"
    kind = "news"

    def __init__(self) -> None:
        self.client = PoliteHttpClient(delay_seconds=settings.request_delay_seconds)

    def fetch(self) -> list[tuple[str, str, str]]:
        payloads: list[tuple[str, str, str]] = []
        for team in settings.active_teams:
            query = quote_plus(f'"{team.team_name}" football player OR roster OR injury OR transfer')
            url = f"https://news.google.com/rss/search?q={query}&hl=en-US&gl=US&ceid=US:en"
            result = self.client.get(url)
            if result and result.status_code == 200:
                payloads.append((team.team_name, url, result.text))
        return payloads

    def parse(self, raw: list[tuple[str, str, str]]) -> list[dict[str, object]]:
        items: list[dict[str, object]] = []
        for team_name, query_url, body in raw:
            parsed = feedparser.parse(body)
            for entry in parsed.entries[: settings.max_news_per_player]:
                items.append({"team": team_name, "query_url": query_url, "entry": entry})
        return items

    def normalize(self, parsed: list[dict[str, object]]) -> dict[str, list[NewsItem]]:
        news: list[NewsItem] = []
        for row in parsed:
            entry = row["entry"]
            title = str(getattr(entry, "title", "")).strip()
            link = str(getattr(entry, "link", "")).strip()
            if not title or not link:
                continue
            summary = short_summary(getattr(entry, "summary", None))
            source_detail = getattr(entry, "source", {})
            source_name = source_detail.get("title", "Google News RSS") if isinstance(source_detail, dict) else "Google News RSS"
            published = parse_datetime(getattr(entry, "published", None))
            text_for_tags = f"{title} {summary or ''}"
            news.append(
                NewsItem(
                    news_id=f"news_{stable_hash(title, link)}",
                    team=str(row["team"]),
                    headline=title,
                    source_name=source_name,
                    source_url=link,
                    published_at=published,
                    summary=summary,
                    tags=classify_news(text_for_tags),
                )
            )
        return {"news": news}

