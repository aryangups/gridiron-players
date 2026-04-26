from cfb_intel.sources.base import Source
from cfb_intel.sources.team_sites import TeamSeedRosterSource


class MockSource(Source):
    source_name = "mock"

    def fetch(self):
        return [{"value": "raw"}]

    def parse(self, raw):
        return [{"value": raw[0]["value"].upper()}]

    def normalize(self, parsed):
        return {"items": parsed}


def test_mock_source_flow():
    assert MockSource().run()["items"][0]["value"] == "RAW"


def test_team_seed_source_has_players():
    result = TeamSeedRosterSource().run()
    assert result["players"]
    assert result["teams"]

