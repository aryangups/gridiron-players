# College Football Player Intel

Production-minded MVP for collecting and publishing public college football player intelligence as repo-native data files.

The pipeline now defaults to a full-FBS run using ESPN's public college football site endpoints for team and roster metadata. It exports normalized player profiles, teams, news metadata, injury-derived updates, a search index, and SQLite snapshots. The source system is modular so future official team-site, stats, RSS, and documented API adapters can be added without rewriting the pipeline.

## What It Collects

- Player roster profiles for the ESPN FBS group, with ESPN roster/profile URLs as provenance.
- Historical player season stats from ESPN's public athlete stats endpoint when available.
- ESPN college football scoreboard, game status, and player box-score stats from public game summary endpoints.
- Team metadata for the full ESPN FBS group.
- Public news metadata from Google News RSS for every collected team when accessible.
- Injury updates extracted conservatively from news items tagged as injury.
- Source URLs and update timestamps on every export record.

## What It Does Not Collect

- Private, login-only, paywalled, or restricted content.
- Full copyrighted articles.
- Medical details unless directly stated in public source metadata.
- Paid API data or secret-key-backed data.

## Ethical Scraping Rules

This project defaults to public feeds and conservative seed roster data. Before enabling any HTML scraper, review robots.txt, site terms, rate limits, and copyright constraints. The HTTP client uses a clear user agent, a 20 second timeout, local caching, retries, backoff, and request delays. Source failures are logged and skipped instead of crashing the full run.

## Setup

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
```

On macOS/Linux, use `source .venv/bin/activate` instead.

CSV export currently uses Python's standard library for portability. Pandas can be added back for heavier cleaning once the runtime has a compatible wheel.

## Run Locally

```bash
python scripts/run_update.py --all
python scripts/validate_data.py
pytest
```

Stage-specific commands:

```bash
python scripts/run_update.py --rosters
python scripts/run_update.py --news
python scripts/run_update.py --injuries
python scripts/build_index.py
```

## Configuration

Configuration lives in [src/cfb_intel/config.py](src/cfb_intel/config.py) and `.env`.

Important flags:

- `ENABLE_GOOGLE_NEWS_RSS=true`
- `ENABLE_TEAM_RSS=true`
- `ENABLE_ESPN=true`
- `ENABLE_SPORTS_REFERENCE=false`
- `ENABLE_NCAA=false`
- `REQUEST_DELAY_SECONDS=0.5`
- `MAX_NEWS_PER_PLAYER=10`
- `MAX_TEAMS_INITIAL_RUN=200`
- `FULL_RUN=true`
- `ESPN_SEASON=2026`
- `ESPN_FBS_GROUP_ID=80`

Set `ENABLE_ESPN=false` to fall back to the five-team seed source. Keep new source adapters disabled until each site is reviewed.

## Exports

Generated files:

- `data/exports/players.json`
- `data/exports/players.csv`
- `data/exports/teams.json`
- `data/exports/player_stats.json`
- `data/exports/espn_cfb_games.json`
- `data/exports/espn_cfb_player_game_stats.json`
- `data/exports/espn_cfb_player_season_totals.json`
- `data/exports/espn_cfb_scoreboard.json`
- `data/exports/espn_cfb.sqlite`
- `data/exports/news.json`
- `data/exports/injuries.json`
- `data/exports/player_index.json`
- `data/exports/cfb_intel.sqlite`

Example player:

```json
{
  "player_id": "cfb_...",
  "full_name": "Arch Manning",
  "team": "Texas",
  "conference": "SEC",
  "position": "QB",
  "status": "active",
  "stats": [
    {
      "season": 2025,
      "team": "Texas Longhorns",
      "passing_yards": 939,
      "passing_tds": 9,
      "source_url": "https://site.web.api.espn.com/apis/common/v3/sports/football/college-football/athletes/..."
    }
  ],
  "source_urls": ["https://texassports.com/sports/football/roster"],
  "last_updated": "2026-04-26T01:00:00Z"
}
```

Example news record:

```json
{
  "news_id": "news_...",
  "player_id": null,
  "headline": "Public RSS headline",
  "source_name": "Publisher",
  "source_url": "https://example.com/article",
  "published_at": "2026-04-26T01:00:00Z",
  "summary": "Short RSS-provided summary only.",
  "tags": ["general"],
  "confidence_score": 0.0
}
```

## GitHub Actions

[.github/workflows/update-data.yml](.github/workflows/update-data.yml) runs every 12 hours and on manual dispatch. It installs dependencies, runs `python scripts/run_update.py --all`, validates exports, and commits changes under `data/exports`, `data/processed`, and `logs` only when data changed.

[.github/workflows/espn-cfb-live.yml](.github/workflows/espn-cfb-live.yml) runs every 10 minutes and polls ESPN's public college football scoreboard/summary endpoints for current game updates. Manual runs can backfill a specific season/week, for example:

```bash
python scripts/run_espn_cfb_update.py --season 2025 --weeks 2 --use-cache
```

For a wider historical backfill:

```bash
python scripts/run_espn_cfb_update.py --season 2025 --weeks regular --use-cache
```

This writes game-level box-score rows to `espn_cfb_player_game_stats.json`, aggregates numeric player season totals to `espn_cfb_player_season_totals.json`, and attaches recent matching ESPN game stat rows to each profile in `players.json` under `game_stats`.

## Add A Source

1. Create a module under `src/cfb_intel/sources/`.
2. Inherit from `Source` and implement `fetch`, `parse`, and `normalize`.
3. Add a feature flag in `config.py`.
4. Register it in `sources/__init__.py`.
5. Add a mocked source test.
6. Document allowed usage, source URLs, and rate limits in `docs/SOURCES.md`.

## Known Limitations

- ESPN endpoints are public but unofficial and may change; the adapter is isolated and can be disabled.
- Official school-site roster scraping is not enabled by default because each site needs separate robots.txt and terms review.
- Player stats are only present when ESPN exposes public stats for that athlete. Players without public stats keep `stats: []`.
- Game-level ESPN CFB stats are box-score rows. They cover players with recorded game stats, not every roster player.
- News matching is heuristic and exposes `confidence_score`.
- Google News RSS may return zero items or fail depending on network and rate limits.

All data should be verified with original source URLs before use in high-stakes contexts.
