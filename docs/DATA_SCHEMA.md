# Data Schema

Schemas are implemented in `src/cfb_intel/schemas.py` with Pydantic.

## Player

Stable identity, roster attributes, source URLs, status, embedded `stats`, and `last_updated`.

## PlayerStats

Season/team row with passing, rushing, receiving, defensive, kicking, and punting fields. Rows are exported separately in `player_stats.json` and embedded into each matching player profile under `stats`.

## NewsItem

Stores metadata only: headline, source, URL, publish timestamp, short summary, tags, optional matched player, and confidence score.

## InjuryUpdate

Derived from injury-tagged news metadata. Status is conservative and defaults to `unknown`.

## Team

Team metadata, official site, roster URL, source URLs, and timestamp.
