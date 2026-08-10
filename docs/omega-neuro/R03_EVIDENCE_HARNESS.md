# Ω-NEURO-CELL-SYN-NET-T∞ — R0.2/R0.3 Evidence Harness

Status: **D-MVP software / E biological hypotheses**.

This layer turns the P1–P7 hypothesis program into a provenance-first benchmark harness. It is designed so that synthetic tests, public datasets and consented datasets can use the same evaluation contract without allowing synthetic success to masquerade as neuroscience evidence.

## R0.2 — provenance and leakage control

Every payload is paired with a `DatasetManifest` containing:

```text
dataset_id
version
source_uri
license_id
access_mode = public | consented | synthetic
sha256
citation
```

The SHA-256 digest binds the manifest to the exact bytes used by an experiment. A changed payload therefore creates a different evidence object.

`group_kfold` partitions by `group_id`, not by row. A cell, subject, preparation, animal, recording session or other experimental unit can therefore be represented as one group and kept entirely on one side of each train/test boundary.

The split itself is hashed into `split_signature`, so a benchmark report identifies both the data bytes and the held-out assignment.

## R0.3 — P1 baseline tournament

The first executable tournament targets **P1 — Dendritic Address Hypothesis**.

For an observation with scalar signal `x`, address `a`, context `c` and target `y`, three nested models are compared:

```text
M0 scalar:
    y ~ x

M1 address-aware:
    y ~ x + I(distal) + I(proximal)
         + x*I(distal) + x*I(proximal)

M2 address + context:
    M1 + c
```

Each model is fitted only on training groups and scored on held-out groups.

Primary predictive loss:

```text
MSE = mean((y_hat - y)^2)
```

OAK selection remains explicit:

```text
J(M) = predictive_loss
     + lambda_C * complexity
     + lambda_U * uncertainty
```

The richer model is justified only when its predictive gain is larger than the extra complexity/uncertainty penalty.

## Ablations

R0.3 automatically tests:

1. `remove_address_interactions`
2. `remove_context`

An ablation is informative only if removing a modeled mechanism degrades held-out prediction. On the synthetic fixture these effects are planted deliberately, so the expected degradation is a software invariant rather than evidence for biology.

## Synthetic fixture rule

The bundled P1 dataset is deterministic and contains a planted address-dependent interaction. It exists to test the evaluator.

Every R0.3 report therefore contains:

```json
{
  "source_class": "synthetic_test_fixture",
  "biological_promotion_allowed": false
}
```

No synthetic result can promote P1 from hypothesis to biological evidence.

## Promotion gate for a real-data adapter

A real dataset enters an empirical P1 tournament only after all of the following are explicit:

- stable source and version identifier;
- exact payload or immutable upstream object hash;
- license/access classification;
- citation/provenance;
- experimental unit mapped to `group_id`;
- target definition fixed before model comparison;
- baseline defined before inspecting candidate performance;
- leakage-safe train/test or cross-validation rule;
- missing-data policy;
- preprocessing record;
- uncertainty and residual report;
- ablations;
- negative controls when possible;
- independent reproduction path.

## Promotion ladder

```text
synthetic pass
    -> software demonstrated

single real dataset pass
    -> empirical signal candidate

replicated dataset / preparation / laboratory pass
    -> stronger evidence

causal intervention + appropriate controls
    -> causal support candidate

formal/experimental convergence
    -> canon review
```

A benchmark score is never itself proof.

## CLI

```bash
omega-neuro-bench --pretty
omega-neuro-bench --groups 32 --trials-per-group 10 --folds 5 --output report.json
python examples/omega_neuro_p1_benchmark.py
```

## Machine-readable artifacts

- `schemas/omega_neuro_dataset_manifest.schema.json`
- report field `manifest.sha256`
- report field `split_signature`
- per-model fold losses
- OAK score comparison
- ablation deltas
- epistemic notice

## OAK / safety boundary

This package is research and model-evaluation infrastructure. It does not diagnose neurological or psychiatric conditions, infer an individual's mental state, recommend treatment, or replace experimental/clinical validation.

The governing rule remains:

```text
biological fact != computational model != Tristan hypothesis
                != prediction != experiment != proof
```
