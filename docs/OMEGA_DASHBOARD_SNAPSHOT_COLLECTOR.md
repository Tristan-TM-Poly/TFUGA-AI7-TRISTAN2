# Ω-DASHBOARD-SNAPSHOT-COLLECTOR

## Mission

The Ω Dashboard Snapshot Collector converts local repository state into a JSON snapshot consumable by the Ω Dashboard Report Generator.

```text
repository files → local dashboard snapshot → dashboard report generator → Markdown/JSON report
```

## Design rules

- Python stdlib only.
- Local filesystem read-only scan.
- No network calls.
- No GitHub/Gmail/web calls.
- No external actions.
- Output is a JSON snapshot only.

## Main command

```bash
python tools/action_dashboard/snapshot_collector.py \
  --root . \
  --out ACTION_DASHBOARD_SNAPSHOT.json
```

Then:

```bash
python tools/action_dashboard/dashboard_report_generator.py \
  ACTION_DASHBOARD_SNAPSHOT.json \
  --markdown-out ACTION_DASHBOARD_REPORT.md \
  --json-out ACTION_DASHBOARD_REPORT.json
```

## What it scans

- `demo_packets/`
- `docs/`
- `orchestration/`
- `tools/`
- `omega_vtp_t/`
- `tests/`
- `.github/workflows/`
- `university_outreach/quebec_universities/`

## Outputs

The collector emits fields aligned with `action_dashboard_schema.yaml`, including:

- active loops;
- lanes;
- proof assets;
- demo packets;
- next best actions;
- safe actions;
- loop upgrades;
- M+ / M− memory;
- external action governor state.

## OAK interpretation

This collector is not a truth oracle. It produces a local repository snapshot. Counts and labels are useful for operational dashboards, but external facts such as real PR status, Gmail replies, and university page changes still require their respective verified connectors or official sources.

## Next upgrades

```text
1. Add GitHub connector snapshot collector.
2. Add Gmail reply snapshot collector.
3. Add university route snapshot collector with official source evidence.
4. Add trend history across dashboard cycles.
5. Add HTML dashboard rendering.
```
