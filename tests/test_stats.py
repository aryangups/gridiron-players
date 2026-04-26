from cfb_intel.pipeline.collect_stats import _rows_from_payload
from cfb_intel.schemas import Player


def test_espn_stats_payload_to_player_stats():
    player = Player(player_id="espn_1", full_name="Test QB", team="Test Team", position="QB", source_urls=["https://example.com"])
    payload = {
        "teams": {"test": {"id": "10", "displayName": "Test Team"}},
        "categories": [
            {
                "name": "passing",
                "names": ["completions", "passingAttempts", "passingYards", "passingTouchdowns", "interceptions", "QBRating"],
                "statistics": [
                    {
                        "teamId": "10",
                        "season": {"year": 2025},
                        "stats": ["10", "20", "200", "2", "1", "145.5"],
                        "position": "QB",
                    }
                ],
            }
        ],
    }
    rows = _rows_from_payload(player, "1", payload)
    assert len(rows) == 1
    assert rows[0].passing_yards == 200
    assert rows[0].passer_rating == 145.5
