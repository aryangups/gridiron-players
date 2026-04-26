# Data Schema

Schemas are implemented in `src/cfb_intel/schemas.py` with Pydantic.

## Player

Stable identity, roster attributes, source URLs, status, embedded `stats`, and `last_updated`.

## PlayerStats

Season/team row with passing, rushing, receiving, defensive, kicking, and punting fields. Rows are exported separately in `player_stats.json` and embedded into each matching player profile under `stats`.

## ESPN CFB Game Stats

`espn_cfb_games.json` stores public ESPN college-football scoreboard rows with game ID, season, week, status, teams, scores, venue, source URL, and update timestamp.

`espn_cfb_player_game_stats.json` stores one row per player/game/stat-category from ESPN game summaries. Each row includes ESPN athlete ID, normalized internal `player_id`, team/opponent context, stat category such as passing/rushing/receiving/defensive/kicking/punting, a source URL, and a `stats` object preserving ESPN's stat keys.

`espn_cfb_player_season_totals.json` aggregates numeric player game-stat values by player, season, and stat category. Composite values such as `18/25` are preserved at the game-stat level but not summed.

Matching ESPN roster players in `players.json` also receive recent rows under `game_stats`.

## NewsItem

Stores metadata only: headline, source, URL, publish timestamp, short summary, tags, optional matched player, and confidence score.

## InjuryUpdate

Derived from injury-tagged news metadata. Status is conservative and defaults to `unknown`.

## Team

Team metadata, official site, roster URL, source URLs, and timestamp.
