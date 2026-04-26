# College Football Player Intel

Production-minded MVP for collecting and publishing public college football player intelligence as repo-native data files.

The pipeline starts small with five configurable teams: Alabama, Georgia, Ohio State, Michigan, and Texas. It exports normalized player profiles, teams, news metadata, injury-derived updates, a search index, and SQLite snapshots. The source system is modular so future roster, stats, RSS, and official API adapters can be added without rewriting the pipeline.

## What It Collects

- Player roster profiles from the MVP roster source with official roster URLs as provenance.
- Team metadata for the configured teams.
- Public news metadata from Google News RSS when accessible.
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
- `ENABLE_ESPN=false`
- `ENABLE_SPORTS_REFERENCE=false`
- `ENABLE_NCAA=false`
- `REQUEST_DELAY_SECONDS=2`
- `MAX_NEWS_PER_PLAYER=10`
- `MAX_TEAMS_INITIAL_RUN=10`
- `FULL_RUN=false`

Expand `MVP_TEAMS` in `config.py` to add teams. Keep source adapters disabled until each site is reviewed.

## Exports

Generated files:

- `data/exports/players.json`
- `data/exports/players.csv`
- `data/exports/teams.json`
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

## Add A Source

1. Create a module under `src/cfb_intel/sources/`.
2. Inherit from `Source` and implement `fetch`, `parse`, and `normalize`.
3. Add a feature flag in `config.py`.
4. Register it in `sources/__init__.py`.
5. Add a mocked source test.
6. Document allowed usage, source URLs, and rate limits in `docs/SOURCES.md`.

## Known Limitations

- MVP roster collection is intentionally small and seed-based to avoid brittle scraping.
- Stats adapters are placeholders for phase 3.
- News matching is heuristic and exposes `confidence_score`.
- Google News RSS may return zero items or fail depending on network and rate limits.

All data should be verified with original source URLs before use in high-stakes contexts.
