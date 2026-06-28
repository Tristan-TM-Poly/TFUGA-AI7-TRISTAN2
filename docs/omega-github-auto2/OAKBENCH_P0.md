# Omega AUTO2 OAKBench P0

OAKBench P0 turns the merged AUTO2 spine into a measurable synthetic benchmark.

## Added files

- `configs/omega_auto2_mminus_registry.json`
- `fixtures/omega_auto2/oakbench/p0_benchmark_suite.json`
- `scripts/omega_auto2_oakbench_p0.py`
- `tests/test_omega_auto2_oakbench_p0.py`

## Purpose

OAKBench P0 checks that the stack remains executable and conservative:

```text
benchmark case
→ run_p0_pipeline
→ compare expected OAK status
→ validate expected next action
→ validate M-minus registry
→ emit OAKBench report
```

## M-minus registry

The registry stores structured negative memory entries with:

- `id`
- `module`
- `failure`
- `detector`
- `severity`
- `example_fixture`
- `anti_rule`
- `oak_action`

## OAK status

This benchmark is synthetic and offline. It does not process private data, call external systems, or claim production readiness.

## CI

The global P0 CI now runs:

```bash
python -m unittest tests/test_omega_auto2_oakbench_p0.py
python scripts/omega_auto2_oakbench_p0.py --output artifacts/omega_auto2/oakbench_p0_report.json
```

## Next action

If OAKBench passes, the next P0 step is a demo pack that produces a stable before/after report without commercial or scientific overclaiming.
