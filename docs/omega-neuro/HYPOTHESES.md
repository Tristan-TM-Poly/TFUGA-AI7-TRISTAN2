# Falsification program — Ω-NEURO-CELL-SYN-NET-T∞

The purpose of this file is to prevent attractive vocabulary from outrunning evidence. Each Tristan hypothesis has a baseline, observable, promotion criterion and failure mode.

## P1 — Dendritic Address Hypothesis

**Hypothesis-T:** knowing where inputs arrive on a modeled dendritic tree improves prediction beyond an address-agnostic aggregation.

**Null:** total/summarized input explains held-out response equally well after controlling model capacity.

**Measure:** held-out predictive loss, calibration and residual structure.

**Promote if:** address-aware improvement survives regularization, matched capacity, ablation, resampling and a second condition/dataset.

**Falsify/limit if:** gain disappears under matched complexity or only reproduces training geometry.

## P2 — Synaptic State Tensor

**Hypothesis-T:** a multidimensional synaptic state predicts transmission/plasticity better than a scalar synaptic weight.

**Null:** extra state dimensions add no generalizable information beyond a scalar baseline.

**Ablations:** release probability, delay, short-term state, long-term state, dendritic address, modulatory context, metabolic context and uncertainty must be removed one at a time and in groups.

**Failure memory:** if a dimension is redundant, unstable or unavailable, remove it from the minimal fertile representation.

## P3 — Higher-Order Wiring

**Hypothesis-T:** motifs involving more than two entities provide predictive information not captured by pairwise edges plus geometry.

**Null:** pairwise connectivity and spatial/structural covariates explain the target equally well.

**Measure:** out-of-sample likelihood/loss, permutation controls, motif enrichment after covariate matching.

**OAK warning:** a hyperedge is not causal evidence merely because a motif is statistically enriched.

## P4 — Morphology–Computation Duality

**Hypothesis-T:** morphological invariants predict selected computational/electrophysiological properties after controlling for cell identity and measurement modality.

**Null:** morphology provides no incremental predictive information after those controls.

**Candidate invariants:** branch-depth distribution, path-length statistics, asymmetry, compartment density, scale-dependent branching descriptors and topology-derived summaries.

**Failure mode:** confounding cell type, preparation, species, acquisition method or reconstruction quality.

## P5 — Dynamic Connectome

**Hypothesis-T:** a context-dependent effective graph predicts instantaneous/short-window function better than the structural graph alone.

**Null:** structural connectivity plus node state is sufficient.

**Model family:** structural + effective + plastic + modulatory + metabolic layers contracted under explicit context.

**Falsifier:** contextual layers fail to improve held-out prediction or cannot reproduce consistently across repeated states.

## P6 — Multiscale NeuroCode

**Hypothesis-T:** multiscale signal invariants contain predictive information not available to matched single-scale features.

**Candidate transforms:** validated standard transforms first; FFWT/CVCD extensions only as additional competitors.

**Required baselines:** raw features, Fourier/STFT/wavelet families as task-appropriate, plus simple statistical summaries.

**Falsifier:** FFWT/CVCD advantage disappears with matched dimensionality, leakage-safe splits or noise/parameter sweeps.

## P7 — Glial Hyperedge

**Hypothesis-T:** explicitly adding measured glial/context variables improves prediction for a defined phenomenon where those variables are biologically relevant.

**Null:** neuronal variables and ordinary covariates are sufficient.

**Promotion:** only phenomenon-specific evidence can promote this. No global claim that glia are required for every computation.

**Falsifier/complexity gate:** if glial variables fail to improve robust prediction, OAK removes the extra structure for that task.

## Common benchmark protocol

For every P1–P7 experiment:

1. preregister target, units, split and evaluation metric;
2. define the simplest credible baseline;
3. define candidate model and incremental information it adds;
4. control leakage and duplicated samples;
5. estimate uncertainty and confidence intervals where appropriate;
6. perform ablations and negative controls;
7. inspect residuals, calibration and subgroup/condition stability;
8. record failed runs in M⁻ rather than deleting them;
9. separate statistical association from causal interpretation;
10. promote only the smallest model whose gain reproduces.

## Evidence ledger fields

```yaml
claim_id: P1..P7
status: MODEL|HYPOTHESIS_T|PREDICTION|ESTABLISHED|EVIDENCE_NEEDED
dataset: string
provenance: string
population_and_scale: string
target: string
baseline: string
candidate: string
metric: string
result: number|null
uncertainty: string|null
confounds: []
ablations: []
negative_controls: []
residuals: []
reproduced: false
promotion: retain|revise|reject|replicate
```
