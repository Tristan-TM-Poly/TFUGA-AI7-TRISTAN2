# Ω-AUTO² OAK Report

## Version

1.1.0

## Added

- AUTO-GENESIS v0.1.
- Genesis tree, scoring, report, and engine modules.
- CLI `genesis` command.
- Genesis tests, fixture, and docs.

## Red locks touched

None by default. AUTO-GENESIS only creates local draft reports.

## External actions added

None.

## Reversibility

All additions are code, docs, tests, and local fixtures. They can be reverted by Git history.

## Required checks

- package version matches CLI version;
- quality-gate passes;
- genesis tests pass;
- tests pass;
- README, CHANGELOG, OAK report, and M-minus report are present.

## OAK decision

v1.1.0 is safe to merge if CI/tests pass because it generates local draft Genesis reports only.
