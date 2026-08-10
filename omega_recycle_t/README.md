# Ω-RECYCLE-T∞ — Structure-Preserving Recycling Lab

R0.4 turns the R0.3 evidence kernel into a circular-flow laboratory that can now expose failures of greedy industrial-symbiosis decisions, solve capacity-limited transport exactly for the declared bipartite network, score probability calibration, bind caller-supplied public-data snapshots to provenance hashes, and apply externally supplied LCIA characterization factors without claiming certification.

Core law:

> Prefer the recovery path that destroys the least useful structure while producing the most future value, subject to measured cost, energy, risk, uncertainty, safety, physical constraints and explicit evidence boundaries.

## R0.4 pipeline

```text
object / waste stream
  -> ResourceGraph + MaterialPassport
  -> route scoring + baselines
  -> exhaustive oracle <-> branch-and-bound
  -> Bayes posterior -> calibration court
  -> industrial offers/needs -> greedy <-> exact regret court
  -> capacity transport min-cost max-flow
  -> public-data snapshot -> provenance hash
  -> LCI inventory -> external LCIA adapter
  -> OAK + M- + reproducible OAKBench
```

## New in R0.4

- exact dependency-free bipartite min-cost maximum-flow transport solver;
- exact industrial-symbiosis matcher using the same compatibility rules as the existing greedy matcher;
- explicit quantity/cost regret report that preserves counterexamples instead of tuning them away;
- weighted Brier score, log loss, reliability bins and expected calibration error;
- public dataset source catalog and deterministic delimited-snapshot ingestion;
- canonical snapshot hashing bound to source URL and retrieval timestamp;
- initial official-source descriptors for Eurostat `env_wasmun` and US EPA SMM Facts and Figures;
- externally supplied, provenance-bound LCIA characterization-factor adapter;
- explicit unmatched-flow reporting and non-certification boundary;
- R0.4 OAKBench courts and CPython 3.11–3.13 CI gates.

## Critical counterexample retained in M-

The R0.2 greedy symbiosis matcher can lose total recoverable flow. R0.4 contains a two-offer/two-need case where greedy recovers 1 unit while the exact court recovers 2. This is kept as a regression test and negative-memory artifact.

## Run

```bash
cd omega_recycle_t
python -m pip install -e .
python -m omega_recycle oakbench
pytest -q
```

## Truth boundaries

- `min_cost_transport` certifies only the declared finite bipartite max-flow/min-cost problem.
- Calibration metrics measure predictive calibration on supplied observations; they do not establish causality, safety or stationarity.
- Dataset hashing establishes byte/record identity after parsing, not truth, comparability or absence of revision.
- The public-source catalog is metadata, not an automatically mirrored authoritative dataset.
- The LCIA adapter ships no endorsed characterization method; factors must be externally supplied with provenance.
- No environmental-superiority, regulatory-compliance or hazardous-processing claim is authorized by the package.

## Promotion path

```text
R0.4 D-MVP++ candidate
 -> R0.5 source-specific Eurostat/EPA adapters + empirical baselines
 -> R0.6 general multi-hop material network + factor-set adapters
 -> R0.7 battery/electronics/building calibration campaigns
 -> R1.0 externally benchmarked decision engine
```

See `docs/DCT_OMEGA_CARD.md`, `docs/R04_EVIDENCE.md`, `docs/PUBLIC_DATASETS.md`, `docs/ARCHITECTURE.md` and `docs/M_MINUS.md`.
