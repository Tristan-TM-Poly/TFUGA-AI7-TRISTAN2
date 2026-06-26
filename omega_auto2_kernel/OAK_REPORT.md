# Ω-AUTO² OAK Report

## Version

0.9.0

## Added

- Local release pipeline.
- CLI `release-check` command.
- Release Markdown/JSON output.
- Release pipeline tests.

## Red locks touched

None.

## External actions added

None.

## Reversibility

All additions are code, docs, tests, and local fixtures. They can be reverted by Git history.

## Required checks

- package version matches CLI version;
- canonical workflows exist;
- quality-gate passes;
- compare passes;
- snapshot and diff pass;
- release-check passes;
- tests pass;
- README, CHANGELOG, OAK report, and M-minus report are present.

## OAK decision

v0.9.0 is safe to merge if CI/tests pass because it only aggregates local checks into a local report.
