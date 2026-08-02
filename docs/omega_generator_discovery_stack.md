# Ω-GENERATOR-DISCOVERY-STACK

## Ten coupled fronts in one OAK-safe executable architecture

**Status:** R0.1 executable scaffold. The package exposes diagnostics and candidate generators; it does not certify causal laws or authorize physical experiments.

## Central pipeline

```text
observation before/after or trajectory
→ type and normalize
→ identify continuous candidate generators
→ detect discrete/singular sectors
→ reconstruct
→ measure residual and semigroup defect
→ design discriminating experiment
→ enforce safety/rollback
→ update evidence state and M-
```

The stack implements all ten fronts requested in one package rather than ten unrelated repositories.

## Front registry

1. `Ω-SPECTRAL-LOGEXP-T`
   - Lorentzian reference generator.
   - Moment-based amplitude, shift, and width candidates.
   - Residual and new-event score.
   - First gate: synthetic shifted/broadened peaks.

2. `Ω-GENERATOR-OPERATOR-T`
   - Fits a scalar affine state propagator.
   - Reports the discrete multiplier, forcing, continuous log-rate, and residual.
   - First gate: out-of-sample affine trajectory.

3. `Ω-SEMIGROUP-RESIDUAL-MICROSCOPE`
   - Computes `||N_2 - N_1^2|| / ||N_2||`.
   - Candidate detector for hidden variables, memory, regime changes, or model failure.
   - A nonzero defect is not automatically evidence of a new physical law.

4. `Ω-CRYSTAL-HOLONOMY-TWIN`
   - Normalized quaternion orientation loops.
   - Reports the loop quaternion, residual angle, and frustration score.
   - The score is not a dislocation density and must be benchmarked against crystal-plasticity and EBSD baselines.

5. `Ω-COMMUTATOR-EXPERIMENT-DESIGNER`
   - Compares `AB` and `BA`.
   - Reports normalized order effect and commutator norm.
   - Intended for protocol design such as heat-then-stress versus stress-then-heat.

6. `Ω-MORPH-COMPILER-T`
   - Compiles typed specifications into `MorphIR`.
   - Keeps continuous generators, discrete events, singular events, invariants, residual, uncertainty, domain, and codomain separate.

7. `Ω-EPISTEMIC-DYNAMICS-T`
   - Computes evidence growth per concept growth.
   - Detects evidence regression, concept expansion without evidence, evidence lag, or crystallization.
   - Counts are navigation metrics, not truth probabilities.

8. `Ω-AUTOLAB-OAK-T`
   - Ranks experiments by residual reduction, generator discrimination, information gain, cost, and risk.
   - Irreversible or high-risk actions are never approved for autonomous execution; the current package only drafts or simulates.

9. `Ω-MORPH-LAB-PROTOCOL`
   - Composable instrument contract.
   - Requires inputs, outputs, generators, safety limits, and rollback steps.
   - The protocol object is a draft, not an instrument command.

10. `Ω-GENERATOR-SYNDROME-T`
    - Compares expected and observed operators.
    - Classifies nominal behavior, continuous drift, or event/model-failure candidates.
    - Designed to connect LOGEXP with ECC, calibration, and maintenance.

## CLI

```bash
omega-generator-discovery affine \
  --source '[0,1,2,3]' \
  --target '[2,5,8,11]'
```

```bash
omega-generator-discovery spectral \
  --axis axis.json \
  --before before.json \
  --after after.json
```

```bash
omega-generator-discovery compile morph.json
omega-generator-discovery epistemic \
  --concepts-before 100 --concepts-after 140 \
  --evidence-before 25 --evidence-after 30
omega-generator-discovery protocol raman_protocol.json
omega-generator-discovery prioritize experiments.json
```

## OAK invariants

- Representability is not compression.
- Compression is not causal explanation.
- Reconstruction is not prediction.
- Prediction is not experimental validation.
- A commutator is order sensitivity in a selected representation.
- A semigroup defect is a diagnostic, not a discovery by itself.
- Holonomy is geometric residue, not automatically a material defect density.
- Spectral moments do not replace physical multi-peak fitting.
- Experiment ranking never authorizes irreversible physical action.
- Every result must preserve units, provenance, uncertainty, and domain of validity before scientific promotion.

## R0.1 tests

The deterministic suite verifies:

- exact affine scale and translation recovery;
- scalar generator rollout;
- exact semigroup consistency;
- noncommuting order effect;
- small generator drift syndrome;
- synthetic Lorentzian shift;
- closed quaternion loop;
- evidence-growth classification;
- AutoLab blocking of irreversible actions;
- protocol rollback requirement;
- typed MorphIR compilation;
- registration of all ten fronts.

## Next coupled releases

### R0.2 — Spectral physics

- analytic Lorentzian/Voigt Jacobians;
- iterative largest-area peak subtraction;
- uncertainty covariance;
- peak birth/death sector;
- derivative-domain and original-domain joint loss;
- baselines against nonlinear least squares.

### R0.3 — General generator identification

- matrix-valued trajectories;
- constrained Lie-algebra bases;
- sparse generator selection;
- BCH/Magnus adaptive order;
- cross-validation and description length.

### R0.4 — Crystal field

- SO(3) branch continuity;
- point-group quotient and minimum disorientation;
- 3D logarithmic strain;
- EBSD grid loops and uncertainty;
- stress/Raman/XRD fusion.

### R0.5 — Autonomous laboratory

- instrument adapters;
- dry-run digital twin;
- expected information gain from posterior models;
- append-only execution ledger;
- explicit human approval queue;
- rollback/compensation recipes.

### R0.6 — Epistemic operating system

- commit and experiment transitions as MorphCodex events;
- claim-equation-code-test-result hyperedges;
- proof-density versus concept-density dashboard;
- automatic M- generation from failed tests;
- OAK promotion and demotion state machine.

## Product paths

1. Spectral analysis SDK for Raman/FTIR/XRD.
2. Generator-discovery research library.
3. OAK scientific-model audit.
4. Crystal digital-twin diagnostics.
5. Instrument protocol and autonomous-lab safety layer.
6. Epistemic GitHub auditor for proof density.
7. Predictive-maintenance generator syndrome API.

No revenue, scientific superiority, or patentability is claimed until measured against explicit baselines and reviewed for IP exposure.
