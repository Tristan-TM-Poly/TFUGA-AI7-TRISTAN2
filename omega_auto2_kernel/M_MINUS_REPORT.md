# Ω-AUTO² M⁻ Report

## Version

0.6.0

## Negative memory learned

| ID | Pattern | Correction |
|---|---|---|
| M-001 | Duplicate GitHub issues | Centralize work in one canonical tracker before creating follow-ups. |
| M-002 | Version drift | Always bump `pyproject.toml`, `__version__`, README, and CHANGELOG together. |
| M-003 | Connector blocks large files | Prefer small modules and incremental commits. |
| M-004 | Branch name drift | Keep branch name aligned with target version when possible. |
| M-005 | Merge before remote CI visibility | Prefer PR + CI; only merge when GitHub reports mergeable and risk is local-only. |
| M-006 | Feature stacking without stabilization | Add quality gate, fixtures, changelog, and OAK report before new large features. |

## Anti-rules

- Do not add external autonomous effects without explicit OAK escalation.
- Do not merge versioned changes without version bump.
- Do not publish or send reports automatically.
- Do not create additional issues unless they are canonical and necessary.
- Do not grow one giant file when the connector blocks content; split into small modules.

## Next M⁻ target

v0.7 should add regression fixtures that compare benchmark outputs across versions.
