# Omega Absorb Poly Prof v1.7

Status: weighted tensor and local answer upgrade.

## Purpose

v1.7 adds weighted professor tensor routes, PolyResearchTwin v3, a local twin answer engine, a department strategy matrix and a route confidence dashboard.

```text
ProfessorTensors
-> weighted routes
-> Twin v3
-> twin answers
-> department matrix
-> route confidence dashboard
```

## New modules

- `professor_tensor_weights.py`
- `poly_research_twin_v3.py`
- `twin_answer_engine.py`
- `department_strategy_matrix.py`
- `route_confidence_dashboard.py`

## CLI commands

```bash
omega-absorb tensor-weights --source combined
omega-absorb twin-answer --source combined --question next-10
omega-absorb department-matrix --source combined
omega-absorb route-dashboard --source combined
```

## Tests

```bash
python examples/omega_absorb_poly_prof_v17_demo.py
python -m pytest tests/test_omega_absorb_poly_prof_v17.py
```

## v1.8 next targets

1. OAK manifest plus;
2. OAK lineage ledger;
3. evidence risk counter;
4. M-minus rules engine;
5. OAK ledger CLI.
