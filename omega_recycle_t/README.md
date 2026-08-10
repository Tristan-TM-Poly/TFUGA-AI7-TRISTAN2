# Ω-RECYCLE-T∞ — Structure-Preserving Recycling Lab

R0.5 advances the R0.4 circular-flow laboratory into a source-aware evidence kernel. It keeps the exact route/symbiosis/transport courts and adds source-specific schema contracts, revision detection, temporal calibration drift, baseline-regret campaigns, exact multi-hop flow and time-expanded flow without claiming that fixtures are live empirical evidence.

Core law:

> Prefer the recovery path that destroys the least useful structure while producing the most future value, subject to measured cost, energy, risk, uncertainty, safety, physical constraints and explicit evidence boundaries.

## R0.5 pipeline

```text
object / waste stream
  -> ResourceGraph + MaterialPassport
  -> route scoring + ablation baselines
  -> exhaustive oracle <-> branch-and-bound
  -> Bayes posterior -> calibration + temporal-drift court
  -> industrial offers/needs -> greedy <-> exact regret court
  -> bipartite transport -> directed multi-hop -> time-expanded flow
  -> Eurostat TSV / EPA normalized bridge
  -> schema + units + status flags + revision detector
  -> provenance snapshot
  -> empirical/negative-control campaign
  -> LCI inventory -> external LCIA adapter
  -> OAK + M- + reproducible evidence reports
```

## New in R0.5

- Eurostat TSV parser that preserves dimensions, time periods, missing values and status flags;
- `env_wasmun` contract requiring `geo`, `unit` and `wst_oper`, with explicit unit normalization;
- EPA SMM normalized bridge with explicit US-short-ton to metric-tonne conversion;
- snapshot revision court for added, removed, modified and structural changes;
- yearly temporal calibration windows and Brier/ECE drift detection;
- weighted prediction campaign harness with MAE, RMSE, bias and canonical regret;
- permanent negative control where the baseline beats the canonical Ω method;
- exact dependency-free directed multi-hop single-commodity min-cost maximum flow;
- time-expanded material-flow network with holdover arcs and no backward-time transfers;
- deterministic CLI `omega-recycle evidence-r05`;
- CPython 3.11–3.13 CI gates preserving all R0.3/R0.4 contracts.

## Permanent M- evidence

R0.4 already retains a case where greedy industrial symbiosis recovers 1 unit while the exact matcher recovers 2. R0.5 adds a second negative control: a prediction campaign where the declared baseline has lower RMSE than the canonical Ω method. Both failures are regression assets and must remain visible.

## Run

```bash
cd omega_recycle_t
python -m pip install -e .
python -m omega_recycle oakbench
python -m omega_recycle evidence-r05
pytest -q
```

## Truth boundaries

- Eurostat parsing validates the declared TSV contract; it does not certify statistical comparability across jurisdictions or revisions.
- The EPA adapter consumes a normalized bridge table. It intentionally does not claim one stable parser for arbitrary EPA HTML, XLS or PDF layouts.
- Fixture-based evidence courts are schema/algorithm regression tests, not live empirical validation.
- Snapshot revision detection identifies record/structure change; it does not decide whether two revisions are semantically comparable.
- Calibration drift measures supplied predictions/outcomes and does not establish causality or guarantee future performance.
- `min_cost_general_flow` and the time-expanded wrapper certify only their finite single-commodity optimization problems.
- Shared-capacity multi-commodity material flow is not implemented in R0.5.
- The LCIA adapter ships no endorsed factor set and does not certify lifecycle conclusions.
- No environmental-superiority, profitability, regulatory-compliance or hazardous-processing claim is authorized by the package.

## Promotion path

```text
R0.5 D-MVP+++ candidate
 -> R0.6 provenance-pinned live snapshots + independent solver cross-checks
       + shared-capacity multi-commodity flow + governed LCIA factor adapters
 -> R0.7 battery/electronics/building empirical campaigns
 -> R1.0 externally benchmarked decision engine
```

See `docs/DCT_OMEGA_CARD.md`, `docs/R05_EVIDENCE.md`, `docs/PUBLIC_DATASETS.md`, `docs/ARCHITECTURE.md` and `docs/M_MINUS.md`.
