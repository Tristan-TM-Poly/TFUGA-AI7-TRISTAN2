# Ω-RECYCLE-T∞ — Structure-Preserving Recycling Lab

R0.2 turns the recycling theory into an executable, OAK-safe research artifact.

Core law:

> Prefer the recovery path that destroys the least useful structure while producing the most future value, subject to cost, energy, risk, uncertainty, safety and physical constraints.

This package does **not** claim a new physical law, does **not** certify lifecycle impact, and does **not** authorize hazardous recycling operations. It is a deterministic decision-support and benchmarking prototype.

## Pipeline

```text
product / waste stream
    -> ResourceGraph + MaterialPassport
    -> candidate recovery routes
    -> value / energy / risk / preservation scoring
    -> local or coupled RecoveryOptimizer
    -> OAK audit
    -> reproducible report
```

The hierarchy encoded by the MVP is a prior, not a hard law:

```text
reuse > repair > remanufacture > component harvest
      > material recycle > energy recovery > disposal
```

A lower-level path can win whenever measured value, cost, quality, risk, constraints or feasibility make it superior.

## What R0.2 implements

- typed Material, Component, RecoveryRoute and RecoveryPlan models;
- ResourceGraph with multi-component hyperedges;
- normalized material-mixture entropy;
- quality-, purity-, contamination-, energy-, risk- and structure-aware scoring;
- deterministic component-wise route optimizer;
- exact small-instance coupled optimizer under cost/energy/risk constraints;
- functional-probability sensitivity and route-switch detection;
- industrial-symbiosis matcher for compatible secondary-material flows;
- UrbanMine spatiotemporal stock aggregation;
- machine-readable MaterialPassport JSON roundtrip;
- OAK gate that explicitly keeps physical execution unauthorized;
- synthetic OAKBench;
- zero-dependency Python package and CLI;
- regression tests and CPython 3.11–3.13 CI.

## Run

```bash
cd omega_recycle_t
python -m pip install -e .
python -m omega_recycle oakbench
```

## Objective

For component i and candidate route r:

J(i,r) = V(i,r) - C(i,r) - λE E(i,r) - λR R(i,r) - X(i,r) + λP P(r) + λF F(i,r).

Local selection uses r*(i) = argmax_r J(i,r). R0.2 also provides an exact small-instance coupled oracle over route combinations subject to declared budgets.

## OAK status

- **Definition:** explicit.
- **Executable artifact:** yes.
- **Synthetic reproducible benchmark:** yes.
- **Local validation:** 14 tests pass in the candidate environment.
- **Physical validation:** no.
- **LCA certification:** no.
- **Industrial superiority claim:** no.
- **Hazardous physical execution:** never authorized by this package.

Target promotion path:

```text
R0.2 D-MVP candidate
 -> R0.3 Bayes uncertainty + scalable constrained solver
 -> R0.4 empirical symbiosis + provenance datasets
 -> R0.5 LCA-compatible inventory adapters + baselines
 -> R1.0 externally benchmarked decision engine
```

See `docs/DCT_OMEGA_CARD.md`, `docs/ARCHITECTURE.md` and `docs/M_MINUS.md`.
