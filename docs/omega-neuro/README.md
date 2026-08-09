# Ω-NEURO-CELL-SYN-NET-T∞

**Status:** X/D-MVP — executable research architecture, not biological proof and not a clinical system.

## Thesis

The useful computational object is not merely a graph of scalar neurons. A more expressive hypothesis class is a hierarchy of coupled systems:

```text
molecules
  -> synaptic nanodomains
  -> dendritic compartments
  -> cells
  -> microcircuits
  -> specialized networks
  -> brain systems
  -> behavior
```

with feedback between scales and with topology, state and plasticity evolving at different rates.

The executable kernel intentionally starts smaller than the biological ambition. It asks whether additional structure buys measurable predictive value over simpler baselines.

## Epistemic contract

Every claim or mechanism should be tagged as one of:

| Tag | Meaning |
|---|---|
| `ESTABLISHED` | grounded in accepted/replicated external evidence; source still required in evidence bundles |
| `MODEL` | explicit mathematical/computational representation |
| `HYPOTHESIS_T` | Tristan hypothesis proposed for testing |
| `PREDICTION` | falsifiable consequence of a model/hypothesis |
| `EVIDENCE_NEEDED` | unresolved or unsupported claim candidate |

Mandatory law:

```text
biological fact != model != Tristan hypothesis != prediction != experimental proof
```

The package never converts a model score into diagnosis, treatment, medical advice, or biological certification.

## Core objects

### NeuroCellState

A compact projection of a potentially much larger state tensor:

```text
X_i(t) = [V, Ca, excitability, metabolism, neuromodulation, uncertainty, ...]
```

It is a model state, not a universal taxonomy of cell types.

### DendriticBranchState

A cell is modeled as a network of local compartments before somatic aggregation:

```text
synaptic inputs -> local branch transformations -> somatic integration -> output
```

The reference `BranchIntegrator` is deliberately transparent and synthetic. The scientific question is whether address-aware compartment models outperform an address-agnostic scalar baseline under held-out evaluation.

### SynapseState

A synapse is represented as a state vector rather than only `w_ij`:

```text
Σ_ij = (
  release_probability,
  quantal_scale,
  delay,
  short_term_gain,
  long_term_gain,
  dendritic_address,
  astrocytic_context,
  neuromodulatory_context,
  metabolic_context,
  uncertainty
)
```

The package exposes both `scalar_weight_baseline()` and `effective_synaptic_weight()` so the additional dimensions must earn their complexity.

### MultiscaleNeuroHypergraph

Relations can connect two or more modeled entities and are separated into layers:

- structural;
- effective;
- plastic;
- modulatory;
- metabolic.

A contextual projection contracts those layers into a task-specific active representation. This is a modeling device; it does not itself establish causal interactions.

### NetworkFingerprint

Specialized networks can be represented by measurable feature vectors rather than only anatomical names: excitation/inhibition proxy, recurrence, modularity, delay dispersion, plasticity, hierarchy and multiscale coherence.

The initial archetypes are synthetic software fixtures, not claims about specific brain regions.

## Hypotheses

The first falsifiable program is defined in [`HYPOTHESES.md`](HYPOTHESES.md):

1. P1 — Dendritic Address Hypothesis
2. P2 — Synaptic State Tensor
3. P3 — Higher-Order Wiring
4. P4 — Morphology–Computation
5. P5 — Dynamic Connectome
6. P6 — Multiscale NeuroCode
7. P7 — Glial Hyperedge

Each must be tested against a null/baseline model and must survive OAK complexity penalties.

## OAKBench

For a candidate model `M`:

```text
J(M) = predictive_loss
     + lambda_complexity * complexity
     + lambda_uncertainty * uncertainty
```

Lower is better. This score is a reproducible decision heuristic, **not proof**.

A richer hypothesis is promoted only when its predictive gain exceeds the complexity/uncertainty cost and remains stable under ablations, alternate splits and suitable external baselines.

## LOG/EXP plasticity

For positive weights, the reference kernel supports a relative-rate parameterization:

```text
rho_w = d(log w)/dt
w(t + dt) = w(t) * exp(rho_w * dt)
```

This exactly linearizes multiplicative updates in log-space. It does **not** imply that all synaptic plasticity or neuronal differential equations become globally linear.

## Package map

```text
omega_neuro_t/
  models.py       typed states + epistemic status + hyperedges
  dendrite.py     branch-local nonlinear reference model
  synapse.py      scalar and contextual synapse projections + LOG update
  hypergraph.py   multiscale multilayer relation model
  networks.py     synthetic network fingerprints/archetypes
  oakbench.py     explicit predictive/complexity/uncertainty gate
  cli.py          deterministic JSON demonstration

tests/test_omega_neuro_t.py
examples/omega_neuro_t_demo.py
docs/omega-neuro/HYPOTHESES.md
docs/omega-neuro/ROADMAP.md
```

## Quick start

```bash
python -m pytest tests/test_omega_neuro_t.py
python -m omega_neuro_t.cli --pretty
omega-neuro --pretty
```

## Promotion gates

A concept moves from X to D only with an executable reproducible artifact. It moves toward C only after:

- external evidence bundle with provenance;
- explicit train/validation/test or equivalent experimental split;
- baseline comparison;
- ablation of extra variables;
- uncertainty and residual analysis;
- robustness across at least one dataset/condition not used to fit the model;
- documented failure cases in M⁻;
- no clinical inference beyond validated scope.

## Safety boundary

This branch is for research modeling, educational analysis, simulations and analysis of appropriately licensed/consented data. It must not be presented as a neurological or psychiatric diagnostic tool, treatment recommendation engine, or substitute for qualified clinical practice.
