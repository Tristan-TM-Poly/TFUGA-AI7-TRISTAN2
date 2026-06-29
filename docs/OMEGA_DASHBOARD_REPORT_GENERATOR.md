# Ω-DASHBOARD-REPORT-GENERATOR

## Mission

The Ω Dashboard Report Generator converts an action-dashboard JSON snapshot into reusable Markdown and normalized JSON reports.

It is the executable bridge between:

```text
Ω-ACTION-LOOP-T → Ω-ACTION-DASHBOARD-T → human-readable OAK report
```

## Design rules

- Python stdlib only.
- JSON input, Markdown/JSON output.
- No external network calls.
- No external actions are executed.
- The report rewards proof accumulation, not raw activity volume.

## Main command

```bash
python tools/action_dashboard/dashboard_report_generator.py \
  examples/action_dashboard/sample_cycle_snapshot.json \
  --markdown-out ACTION_DASHBOARD_REPORT.md \
  --json-out ACTION_DASHBOARD_REPORT.json
```

## Input snapshot

The snapshot may include:

- active loops;
- blockers;
- next best actions;
- lane state;
- proof assets;
- merged PRs;
- demo packets;
- official routes;
- M+ / M− memory;
- external action governor state.

## Output sections

```text
Metrics
Next Best Actions
Blockers
Lanes
M+ / M- Memory
External Action Governor
OAK Summary
```

## OAK interpretation

The generator is read-only and internal. It does not send emails, merge PRs, submit forms, publish claims, or change external systems. It only transforms current-state snapshots into decision reports.

## Next upgrades

```text
1. Auto-generate snapshots from GitHub/Gmail/university registers.
2. Persist dashboard report artifacts in reports/action_dashboard/.
3. Add trend comparison between cycles.
4. Add Proof Capital and Friction Burn Rate graphs.
5. Add CI workflow for generator tests.
```
