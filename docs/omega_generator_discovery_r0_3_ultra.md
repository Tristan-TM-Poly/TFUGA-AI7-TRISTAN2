# Ω-GENERATOR-DISCOVERY R0.3 Ultra

## 393,216 linked research records with no permanent total ceiling

**Status:** executable infrastructure and generated candidate atlas. This release does not claim 65,536 discoveries, 131,072 experiments, or any new physical law.

## 1. Purpose

R0.3 Ultra replaces flat volume growth with a linked research fabric:

```text
generator candidate
├── 2 synthetic benchmark specifications
├── 1 ordered-composition hyperedge
├── 1 mandatory negative control
└── 1 validation-ledger decision
```

The default finite profile contains:

| Record class | Count |
|---|---:|
| Generator candidates | 65,536 |
| Benchmark specifications | 131,072 |
| Composition hyperedges | 65,536 |
| Negative controls | 65,536 |
| Validation decisions | 65,536 |
| **Total JSONL records** | **393,216** |

The total is produced from configurable axes:

\[
32\text{ domains}
\times 32\text{ families}
\times 8\text{ scales}
\times 4\text{ representations}
\times 2\text{ regimes}
=65,536.
\]

There is no `MAX_ADDITIONS` constant. Enlarging any axis creates a larger finite experiment. Physical storage, CI time, provider quotas, quality gates, cost and rollback remain real constraints.

## 2. Axes

### Domains

Spectral, crystal, elastic, thermal, electromagnetic, chemical, quantum, stochastic, fluid, battery, optical, photonic, acoustic, biological, ecological, climate, materials, calibration, control, robotics, computing, neural, epistemic, software, economic, energy, transport, geological, astronomical, linguistic, social and game systems.

### Generator families

Translation, dilation, rotation, shear, diffusion, advection, reaction, relaxation, oscillation, coupling, projection, lift, convolution, deconvolution, phase shift, amplitude, broadening, splitting, merging, branching, threshold, saturation, hysteresis, memory, symmetry breaking, topology change, rank change, noise, measurement, control, correction and compression.

### Scales

Atomic, molecular, micro, meso, macro, system, network and multiscale.

### Representations

- state;
- operator;
- observable;
- hypergraph.

### Regimes

- local linear;
- finite nonlinear.

## 3. Generator record

Each generator contains:

- typed coordinates;
- operator DSL candidate;
- parameter schema;
- epistemic status;
- invariant candidate;
- risk and risk tier;
- inverse support;
- discrete/singular-sector requirements;
- eight mandatory OAK gates;
- exact links to its benchmarks, hyperedge, negative control and validation record.

Example conceptual record:

```json
{
  "id": "GEN3-000000",
  "coordinates": {
    "domain": "spectral",
    "family": "translation",
    "scale": "atomic",
    "representation": "state",
    "regime": "local_linear"
  },
  "operator_dsl": "exp(theta_0 * partial_axis)",
  "epistemic_status": "machine_generated_candidate_not_evidence"
}
```

## 4. Benchmarks

Each generator receives two linked specifications:

1. nominal;
2. perturbed.

They contain deterministic seeds, parameters, expected reconstruction bounds, an invariant candidate and a baseline declaration.

These are **test specifications**, not measured results. An implementation still has to execute them against a real generator, simulator or dataset.

## 5. Ordered-composition hyperedges

Each generator is linked to a second family in the same domain, scale, representation and regime.

The hyperedge stores:

```text
path A = left then right
path B = right then left
compare = normalized final-state residual
```

This supports future BCH, Magnus and commutator experiments. A nonzero result establishes order sensitivity in the selected representation, not fundamental causality.

## 6. Negative controls

Every generator has one mandatory wrong-family control. The control succeeds only if the candidate family outperforms or rejects the wrong family under explicit metrics.

Failure to reject the negative control signals:

- non-identifiability;
- an over-flexible basis;
- insufficient data;
- a bad metric;
- a hidden variable;
- or a false interpretation.

## 7. Adaptive validation

Validation is risk-sensitive:

- **high risk:** exhaustive validation required;
- **medium risk:** deterministic stratified sampling, with exhaustive escalation triggers;
- **low risk:** deterministic stratified sampling.

No record is promoted automatically. Every validation record contains:

```json
{
  "promotion_allowed": false,
  "promotion_blocker": "real_data_and_domain_expert_review_required"
}
```

## 8. Storage architecture

```text
generated/omega_generator_discovery_r03_ultra/
├── catalogs/
├── benchmarks/
├── hyperedges/
├── negative_controls/
├── validation/
├── index/
│   └── omega_generator_r03_ultra.sqlite3
├── manifest.json
└── README.md
```

JSONL shards preserve streaming, reviewable diffs and deterministic regeneration. SQLite adds indexed queries and cross-link audits.

## 9. Determinism

The generator:

1. writes every shard from a versioned configuration;
2. computes a combined SHA-256 fingerprint;
3. builds the SQLite index;
4. audits counts, links and validation rules;
5. regenerates a second time in CI;
6. refuses the commit if fingerprints differ.

## 10. CLI

Statistics:

```bash
omega-generator-ultra stats
```

Full audit:

```bash
omega-generator-ultra audit
```

Filtered query:

```bash
omega-generator-ultra query \
  --domain spectral \
  --family translation \
  --scale micro \
  --representation operator \
  --regime local_linear \
  --limit 20
```

Linked bundle:

```bash
omega-generator-ultra bundle GEN3-000000
```

Risk-aware validation sample:

```bash
omega-generator-ultra sample --modulus 16 --residue 0
```

Export a reproducible sub-atlas:

```bash
omega-generator-ultra export generated/subatlas.jsonl \
  --domain crystal \
  --family rotation \
  --limit 64
```

## 11. Regeneration

```bash
python tools/generate_omega_generator_r03_ultra.py --root .
```

The current profile is configured in:

```text
configs/omega_generator_r03_ultra.json
```

Changing axes changes the finite experimental frontier. No total ceiling is embedded in the compiler.

## 12. OAK boundary

The following implications are forbidden:

```text
record count -> truth
record count -> novelty
record count -> patentability
record count -> market value
shared name -> cross-domain physical identity
commutator -> fundamental causal interaction
logarithmic fit -> physical law
synthetic benchmark -> empirical validation
```

Scientific promotion requires:

- explicit units;
- source provenance;
- domain of validity;
- baseline comparison;
- uncertainty quantification;
- negative-control success;
- reconstruction;
- out-of-sample prediction;
- falsification attempt;
- domain-expert review;
- reproduction or a strong replication plan.

## 13. Next expansions

### R0.4 — Executable bases

- concrete translation, dilation, rotation, diffusion and reaction operators;
- sparse basis identification;
- automatic differentiation or analytic Jacobians;
- BCH/Magnus convergence gates;
- numerical conditioning and branch ledgers.

### R0.5 — Real spectroscopy and crystals

- Raman, FTIR and XRD datasets with provenance;
- Lorentzian/Voigt iterative deconvolution;
- EBSD orientation grids;
- SO(3) branch continuity;
- point-group quotient;
- stress, temperature and phase fusion.

### R0.6 — Distributed atlas

- Parquet and partitioned SQLite;
- graph index;
- content-addressed shards;
- distributed checkpoints;
- differential regeneration;
- validation budgets and backpressure;
- M⁺ and M⁻ ledgers.

### R0.7 — AutoLab digital twin

- expected information gain;
- simulator-only experiment selection;
- explicit approval queue;
- append-only execution ledger;
- rollback and compensation recipes;
- no irreversible act without human approval.

## 14. Canonical statement

R0.3 Ultra is not a claim that everything has been discovered. It is a scalable machine for ensuring that every candidate has a place, explicit links, a counter-test, a validation decision and an epistemic boundary.

The target is not maximum text. The target is maximum **structured optionality under proof discipline**.
