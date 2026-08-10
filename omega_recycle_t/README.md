# Ω-RECYCLE-T∞ — Structure-Preserving Recycling Lab

R0.1 turns the recycling theory into an executable, OAK-safe research artifact.

Core law:

> Prefer the recovery path that destroys the least useful structure while producing the most future value, subject to cost, energy, risk, uncertainty, safety and physical constraints.

This package does **not** claim a new physical law, does **not** certify lifecycle impact, and does **not** authorize hazardous recycling operations. It is a deterministic decision-support and benchmarking prototype.

## Pipeline

```text
product / waste stream
    -> ResourceGraph + MaterialPassport
    -> candidate recovery routes
    -> value / energy / risk / preservation scoring
    -> RecoveryOptimizer
    -> OAK audit
    -> reproducible report
```

The hierarchy encoded by the MVP is:

```text
reuse > repair > remanufacture > component harvest
      > material recycle > energy recovery > disposal
```

The ordering is a *prior*, not a hard rule. A lower-level path can win whenever measured value, cost, quality, risk or feasibility makes it superior.

## What R0.1 implements

- typed Material, Component, RecoveryRoute and RecoveryPlan models;
- ResourceGraph with multi-component hyperedges;
- normalized material-mixture entropy;
- quality-, purity-, contamination-, energy-, risk- and structure-aware scoring;
- deterministic route optimizer;
- machine-readable MaterialPassport JSON roundtrip;
- OAK gate that explicitly keeps physical execution unauthorized;
- synthetic OAKBench;
- zero-dependency Python package and CLI;
- regression tests.

## Run

```bash
cd omega_recycle_t
python -m pip install -e .
python -m omega_recycle oakbench
```

or:

```bash
omega-recycle oakbench
```

## Objective

For component i and candidate route r, R0.1 uses a transparent utility:

J(i,r) = V(i,r) - C(i,r) - λE E(i,r) - λR R(i,r) - X(i,r) + λP P(r) + λF F(i,r).

The optimizer selects r*(i) = argmax_r J(i,r).

R0.1 is intentionally component-wise. Coupled plant capacity, routing, inventory, uncertain prices, stochastic degradation and multi-period industrial symbiosis belong to later releases.

## OAK status

- **Definition:** explicit.
- **Executable artifact:** yes.
- **Synthetic reproducible benchmark:** yes.
- **Physical validation:** no.
- **LCA certification:** no.
- **Industrial superiority claim:** no.
- **Hazardous physical execution:** never authorized by this package.

Target promotion path:

```text
R0.1 D-MVP
 -> R0.2 coupled-flow optimizer
 -> R0.3 uncertainty + Bayes
 -> R0.4 industrial-symbiosis matcher
 -> R0.5 public datasets + baselines
 -> R1.0 experimentally benchmarked decision engine
```

See `docs/DCT_OMEGA_CARD.md` and `docs/M_MINUS.md`.
