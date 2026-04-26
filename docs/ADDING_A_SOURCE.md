# Adding A Source

1. Review legal and ethical access rules for the source.
2. Add a feature flag to `config.py`.
3. Create a `Source` subclass in `src/cfb_intel/sources/`.
4. Implement `fetch()`, `parse()`, `normalize()`, and set `source_name`, `source_url`, `kind`, and `enabled`.
5. Return Pydantic models, not raw dictionaries, from `normalize()`.
6. Register the source in `src/cfb_intel/sources/__init__.py`.
7. Add tests with mocked HTTP responses.
8. Update `docs/SOURCES.md`.

Source failures must be non-fatal. If a site returns 403 or 429, log and skip it.

