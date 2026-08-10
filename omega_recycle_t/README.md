# Ω-RECYCLE-T∞ — Structure-Preserving Recycling Lab

R0.3 turns the R0.2 recovery kernel into a more falsifiable decision engine: the original exhaustive coupled solver is retained as a small-instance oracle, while an auditable branch-and-bound solver, explicit counterfactual baselines, Bayesian functional-state uncertainty, LCA-shaped inventories, domain UrbanMine adapters and provenance hashes are added around it.

Core law:

> Prefer the recovery path that destroys the least useful structure while producing the most future value, subject to measured cost, energy, risk, uncertainty, safety and physical constraints.

The hierarchy

```text
reuse > repair > remanufacture > component harvest
      > material recycle > energy recovery > disposal
```

is an explicit prior, not a law. R0.3 therefore benchmarks the canonical policy against mass-only, value-only and no-preservation-prior counterfactuals.

## R0.3 pipeline

```text
object / waste stream
  -> ResourceGraph + MaterialPassport + provenance
  -> candidate routes
  -> canonical score + explicit baselines
  -> exact small-instance oracle <-> branch-and-bound cross-check
  -> Bayesian functional-state propagation
  -> LCA-shaped inventory (not LCIA)
  -> UrbanMine / electronics / battery / building adapters
  -> OAK audit + M- registry
  -> reproducible OAKBench
```

## New in R0.3

- `BranchAndBoundRecoveryOptimizer` with admissible score upper bound;
- finite `SearchBudget` that returns an incumbent without falsely claiming optimality;
- exact-oracle cross-check on small coupled problems;
- mass-only, value-only and preservation-ablation baselines;
- Beta posterior for component functional probability;
- deterministic seeded posterior route-preference sampling;
- inventory-only LCA interface with explicit no-impact-assessment claim boundary;
- ElectronicsMine, BatteryMine and BuildingMine adapters into `UrbanMine`;
- canonical dataset hashing and provenance record primitives;
- OAKBench R0.3 evidence for solver agreement and claim boundaries.

## Run

```bash
cd omega_recycle_t
python -m pip install -e .
python -m omega_recycle oakbench
pytest -q
```

## Solver truth contract

The R0.2 `ConstrainedRecoveryOptimizer` remains the exhaustive oracle. R0.3 branch-and-bound is considered correct on a benchmark only when it reproduces the oracle's score and selected modes.

A finite search budget may terminate early. In that case:

```text
optimality_certified = false
```

and the returned plan is only an incumbent.

Branch-and-bound remains exponential in the worst case; R0.3 does not claim a polynomial-time industrial optimizer.

## OAK claim boundary

R0.3 demonstrates executable software and synthetic reproducible cross-checks. It does **not** establish industrial superiority, real lifecycle benefit, regulatory compliance, safe hazardous processing, calibrated failure probabilities, or a new physical law.

The LCA layer is an inventory interface only. Environmental impact claims require external inventory data, characterization factors, system boundaries and a recognized LCA methodology.

## Promotion path

```text
R0.3 D-MVP+
 -> R0.4 provenance-tracked public datasets + exact/greedy symbiosis regret
 -> R0.5 scalable capacity/transport network optimization + LCIA adapters
 -> R0.6 empirical battery/electronics/building mine calibration
 -> R1.0 externally benchmarked decision engine
```

See `docs/DCT_OMEGA_CARD.md`, `docs/R03_EVIDENCE.md`, `docs/ARCHITECTURE.md` and `docs/M_MINUS.md`.
