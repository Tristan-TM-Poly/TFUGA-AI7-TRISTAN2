# Ω-LEARN-T v0.2 status

This branch upgrades Ω-LEARN-T from a diagnostic MVP to a persistent learning-loop prototype.

## Implemented

- JSONL state store.
- Review queue scheduler.
- CSV/JSON/Markdown exporters.
- GitHub issue markdown bridge.
- CLI integration for persistence, queue and exports.
- Issue templates.
- Minimal v0.2 tests.

## Local validation

The expanded local package was tested with:

```bash
python -m pytest -q
# 9 passed
```

## GitHub validation note

The branch contains minimal v0.2 tests plus the original v0.1 tests. The full downloadable local artifact includes the expanded suite and generated package zip.
