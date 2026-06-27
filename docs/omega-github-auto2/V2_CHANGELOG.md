# Omega GitHub AUTO2 v2 Changelog

## Upgraded in PR #107

- Converted factory from simple card generator to v2 reactor artifact factory.
- Added Top16 immediate execution queue.
- Added Top64 execution queue with OAK/disclosure/review metadata.
- Added dashboard generation.
- Added OAK tribunal report.
- Added dependency graph generation.
- Added GitHub label manifest generation.
- Added repo routing manifest generation.
- Added M-minus registry seed.
- Added issue draft factory.
- Added PR draft factory.
- Added Codex task factory.
- Added v2 E-cap score model.
- Added card disclosure levels.
- Added state machine config.
- Converted tests to `unittest` so the workflow command actually executes them.
- Added issue template for Omega AUTO2 cards.
- Added human lock, OAK tribunal, card contract, scoring, and roadmap docs.

## Known limitation

The formal JSON Schema file was not added because the connector blocked that exact payload. The card contract is therefore documented in Markdown and enforced by the factory/tests for now.

## Next v3 target

A manual, rate-limited issue materializer may be added later. It should never auto-merge or mass-open unreviewed sensitive work.
