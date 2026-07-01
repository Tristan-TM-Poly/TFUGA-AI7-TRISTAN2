# FixAll Batch M+ Registry

## Successful patterns

- Local dry-run summaries reduce manual repeated inspection.
- Fixture-driven validation protects the decision schema.
- Separate Markdown and JSON outputs support both human review and machine routing.
- PR-only CI avoids changing push behavior until the module is trusted.

## Next improvement

A future layer can ingest live observed PR states into decision JSON files, but that must remain dry-run first.
