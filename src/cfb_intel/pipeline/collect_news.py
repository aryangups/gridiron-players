"""News collection and player matching."""

from __future__ import annotations

from cfb_intel.config import settings
from cfb_intel.schemas import NewsItem, Player, Team
from cfb_intel.sources.rss_news import GoogleNewsRssSource
from cfb_intel.utils.text import normalize_name


def match_news_to_players(news_items: list[NewsItem], players: list[Player]) -> list[NewsItem]:
    by_full = {normalize_name(player.full_name): player for player in players}
    matched: list[NewsItem] = []
    for item in news_items:
        text = normalize_name(f"{item.headline} {item.summary or ''}")
        best_player: Player | None = None
        best_score = 0.0
        for player in players:
            full = normalize_name(player.full_name)
            last = normalize_name(player.last_name or "")
            team_match = player.team.lower() in (item.team or "").lower() or player.team.lower() in item.headline.lower()
            if full in text and team_match:
                best_player, best_score = player, 0.95
                break
            if full in text and best_score < 0.75:
                best_player, best_score = by_full[full], 0.75
            elif last and last in text and team_match and best_score < 0.55:
                best_player, best_score = player, 0.55
        if best_player:
            item = item.model_copy(
                update={
                    "player_id": best_player.player_id,
                    "player_name": best_player.full_name,
                    "team": best_player.team,
                    "confidence_score": best_score,
                }
            )
        matched.append(item)
    return matched


def collect_news(players: list[Player], teams: list[Team] | None = None) -> dict[str, list[NewsItem]]:
    news_items: list[NewsItem] = []
    if settings.enable_google_news_rss:
        team_names = sorted({team.team_name for team in teams or []}) or sorted({player.team for player in players})
        result = GoogleNewsRssSource(team_names=team_names).run()
        news_items.extend(result.get("news", []))
    return {"news": match_news_to_players(news_items, players)}
