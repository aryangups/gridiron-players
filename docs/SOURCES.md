# Sources

## Current MVP

- MVP official-roster seed: small player set for configured teams, each with official team roster URL provenance.
- Google News RSS: public RSS metadata only, disabled by setting `ENABLE_GOOGLE_NEWS_RSS=false`.

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

