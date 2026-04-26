from datetime import datetime, timezone

from cfb_intel.pipeline.espn_cfb_live import (
    _game_from_event,
    _stat_value,
    aggregate_player_season_totals,
)
from cfb_intel.schemas import EspnCfbPlayerGameStat


def test_stat_value_parser():
    assert _stat_value("1,268") == 1268
    assert _stat_value("7.5") == 7.5
    assert _stat_value("11/22") == "11/22"
    assert _stat_value("--") is None


def test_game_from_event():
    game = _game_from_event(
        {
            "id": "401752815",
            "date": "2025-09-06T19:30Z",
            "name": "Grambling Tigers at Ohio State Buckeyes",
            "shortName": "GRAM @ OSU",
            "season": {"year": 2025, "type": 2},
            "week": {"number": 2},
            "competitions": [
                {
                    "venue": {"fullName": "Ohio Stadium"},
                    "status": {"period": 4, "clock": 0, "type": {"description": "Final", "state": "post"}},
                    "competitors": [
                        {"homeAway": "home", "score": "70", "team": {"id": "194", "displayName": "Ohio State Buckeyes"}},
                        {"homeAway": "away", "score": "0", "team": {"id": "2755", "displayName": "Grambling Tigers"}},
                    ],
                }
            ],
        }
    )
    assert game is not None
    assert game.home_team == "Ohio State Buckeyes"
    assert game.home_score == 70
    assert game.week == 2


def test_aggregate_player_season_totals():
    row = EspnCfbPlayerGameStat(
        stat_id="s1",
        game_id="g1",
        season=2025,
        game_date=datetime.now(timezone.utc),
        player_id="espn_1",
        espn_athlete_id="1",
        player_name="Test Player",
        team_id="espn_194",
        team="Ohio State Buckeyes",
        stat_type="passing",
        stats={"passingYards": 250, "completions_passingAttempts": "18/25"},
        source_url="https://site.api.espn.com/apis/site/v2/sports/football/college-football/summary?event=g1",
    )
    totals = aggregate_player_season_totals([row])
    assert totals[0]["stats"]["passingYards"] == 250
    assert totals[0]["games_with_stat"] == 1
