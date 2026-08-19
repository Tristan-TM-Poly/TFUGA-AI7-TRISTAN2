# ARK-SP-CUBE-GAIA v0.14 Track Backlog

Status: `C_plus_local_backlog_only`

This backlog prepares diversification PRs without creating remote issues automatically.

## Rule

```text
Each follow-up PR must carry one measurable path and one OAK failure path.
```

## Backlog cards

### D1-SPCUBE-LAB

- Build a passive plate CSV schema.
- Define baseline samples and required environmental fields.
- Add example rows with fake values only if clearly marked simulated.
- OAK failure: no measured delta-T advantage.

### D2-ARK-M1-BENCH

- Add BOM for low-power bench.
- Add safe wiring and cutoff checklist.
- Add sensor channel map.
- OAK failure: unsafe heating, unstable power, sensor drift or no usable comparison.

### D3-METHANE-MRV

- Expand event registry with before/repair/after fields.
- Add duplicate-key logic concept.
- Add uncertainty and source-type fields.
- OAK failure: missing repair proof, duplicate event, source attribution failure.

### D4-OAK-TOOLING

- Convert OAK-Lint rules into runnable CLI.
- Add fixture texts: safe, warn, block.
- Add validation report format.
- OAK failure: unsafe claim passes lint.

### D5-PUBLIC-DASHBOARD

- Create static portfolio dashboard.
- Add proof-level cards and non-claim cards.
- Add status badges for IDEA/SIMULATED/MEASURED/CERTIFIED.
- OAK failure: dashboard implies certification, revenue or investment readiness.

### D6-THESIS-PATENT-ROUTE

- Create claim tree template.
- Add novelty/risk/evidence placeholders.
- Add review-card format.
- OAK failure: legal validity implied without review.

### D7-INFRA-GOV-GRAPH

- Map GAIA event to graph nodes/edges.
- Add local severity route.
- Add proof-edge examples.
- OAK failure: official decision authority implied.

### D8-SENSOR-LOGGER

- Add ESP32/Python logging route.
- Add CSV schema for timestamp, temperature, power and weather fields.
- Add calibration TODO fields.
- OAK failure: uncalibrated logging treated as certified measurement.

### D9-SOURCES

- Create verified source registry structure.
- Link each public claim to source/TODO.
- Add access date and claim scope.
- OAK failure: claim remains public without source or TODO label.

### D10-FAILURESYNTH

- Expand failure mode table.
- Link each failure to lint rule and issue draft.
- Add severity P0-P3.
- OAK failure: failure is vague or not actionable.

## Next operating mode

Prefer 3-5 small PRs instead of one large mega-PR:

1. `v0.15-oak-tooling-cli`
2. `v0.15-spcube-ark-logger-schema`
3. `v0.15-methane-mrv-schema`
4. `v0.15-public-safe-dashboard`
5. `v0.15-sources-and-failure-routes`
