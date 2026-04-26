from datetime import datetime, timezone

from cfb_intel.pipeline.collect_news import match_news_to_players
from cfb_intel.schemas import NewsItem, Player
from cfb_intel.utils.text import classify_news, normalize_name


def test_name_normalization():
    assert normalize_name("Anthony Hill Jr.") == "anthony hill"


def test_news_to_player_matching():
    player = Player(player_id="p1", full_name="Arch Manning", team="Texas", position="QB", source_urls=["https://example.com"])
    news = NewsItem(
        news_id="n1",
        headline="Arch Manning named Texas starter",
        source_name="Example",
        source_url="https://example.com",
        published_at=datetime.now(timezone.utc),
    )
    matched = match_news_to_players([news], [player])[0]
    assert matched.player_id == "p1"
    assert matched.confidence_score >= 0.75


def test_news_classification():
    assert "injury" in classify_news("QB questionable with knee injury")

