from datetime import datetime, timezone

from cfb_intel.schemas import InjuryUpdate, NewsItem, Player, PlayerStats


def test_player_schema_validation():
    player = Player(
        player_id="p1",
        full_name="Arch Manning",
        team="Texas",
        stats=[{"season": 2025, "passing_yards": 100}],
        source_urls=["https://example.com"],
    )
    assert player.full_name == "Arch Manning"
    assert player.stats[0]["season"] == 2025


def test_stats_schema_validation():
    stats = PlayerStats(player_id="p1", season=2025, team="Texas", source_url="https://example.com")
    assert stats.season == 2025


def test_news_schema_validation():
    item = NewsItem(
        news_id="n1",
        headline="Texas QB throws touchdown",
        source_name="Example",
        source_url="https://example.com",
        published_at=datetime.now(timezone.utc),
    )
    assert item.tags == ["general"]


def test_injury_schema_validation():
    injury = InjuryUpdate(
        injury_id="i1",
        player_name="Arch Manning",
        report_text_summary="Player is questionable",
        source_name="Example",
        source_url="https://example.com",
        reported_at=datetime.now(timezone.utc),
    )
    assert injury.injury_status == "unknown"
