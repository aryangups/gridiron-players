# Sources

## Current Full-FBS Source

- ESPN public site/core endpoints: full ESPN FBS group team list, roster metadata, and public athlete historical stats. Enabled by `ENABLE_ESPN=true` and `ENABLE_PLAYER_STATS=true`.
- Google News RSS: public RSS metadata only for each collected team. Disabled by setting `ENABLE_GOOGLE_NEWS_RSS=false`.

The ESPN adapter uses public JSON endpoints that power ESPN's college football pages. They are not a contracted API and may change, so the source is isolated in `src/cfb_intel/sources/espn.py` and can be disabled without changing the rest of the pipeline.

## Fallback MVP Source

- MVP official-roster seed: small player set for configured teams, used when `ENABLE_ESPN=false`.

## Disabled Placeholders

- ESPN
- Sports Reference / College Football Reference
- NCAA public stats

Enable these only after reviewing current terms, robots.txt, public endpoint behavior, and appropriate rate limits.

## Source Rules

- Prefer official APIs, RSS, public datasets, and documented endpoints.
- Do not collect private, login-only, paywalled, or restricted content.
- Do not store full articles.
- Include source URL and timestamp whenever possible.
- Log skipped and failed sources.
