from cfb_intel.pipeline.dedupe import dedupe_players
from cfb_intel.schemas import Player


def test_player_deduplication():
    players = [
        Player(player_id="p1", full_name="Arch Manning", team="Texas", position="QB", source_urls=["https://a.example"]),
        Player(player_id="p2", full_name="Arch Manning", team="Texas", position="QB", source_urls=["https://b.example"]),
    ]
    deduped = dedupe_players(players)
    assert len(deduped) == 1
    assert len(deduped[0].source_urls) == 2

