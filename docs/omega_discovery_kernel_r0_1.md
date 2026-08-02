# Ω-DISCOVERY-KERNEL-T∞ R0.1

**Status:** executable closed-loop event ledger / OAK-safe workflow kernel / not scientific certification.

## 1. Purpose

The repository already contains four complementary capabilities:

- WikiForge and universal absorbers for traceable observations and source material;
- Ω-HYPERKNOWLEDGE-T∞ for atomic claims, evidence, counterevidence, OAK history, and M⁻;
- Ω-GENERATOR-DISCOVERY-STACK for candidate operators, residuals, experiments, protocols, and syndromes;
- Ω-SANS-PLAFOND-T∞ for adaptive streaming, sharding, checkpointing, and reviewable GitHub plans.

R0.1 supplies the missing common language that connects these systems into one recorded loop.

```text
ObservationEvent
→ ClaimEvent
→ GeneratorCandidate
→ ExperimentSpec
→ ResultPacket
→ OAKTransition
→ MMinusRule
→ ActionProposal
```

A complete chain proves only that the workflow was recorded and passed structural gates. It does not prove the claim, establish causality, certify a physical law, guarantee safety, or establish product value.

## 2. Canonical event envelope

Every event carries:

```yaml
event_id:
event_type:
subject_id:
timestamp:
parent_ids:
source_hash:
provenance:
domain:
status:
payload:
units:
uncertainty:
human_approval:
reversible:
event_hash:
```

The event identifier is deterministic for the canonical content. The event hash is recomputed during validation, making silent payload modification detectable.

The ledger itself has a root hash over the ordered event hashes.

## 3. Eight event types

### ObservationEvent

Records what was observed, imported, measured, or extracted. It should include exact provenance, source hashes, units, uncertainty, calibration context, and acquisition conditions whenever applicable.

It does not contain an automatic interpretation.

### ClaimEvent

Records an atomic proposition with scope, assumptions, polarity, and failure conditions. It must descend from an observation.

A claim is not proof.

### GeneratorCandidate

Records a candidate transformation model, usually compiled from `MorphIR`. It keeps continuous generators, discrete events, singular events, invariants, residual, and uncertainty distinct.

Representability is not compression. Reconstruction is not prediction. Prediction is not causal explanation.

### ExperimentSpec

Records a discriminating experiment, baseline, metric, threshold, safety limits, and rollback procedure. It must descend from a generator candidate.

An irreversible experiment requires explicit human approval.

### ResultPacket

Records the result of a declared experiment, including the protocol, metric, threshold, baseline, units, uncertainty, and success flag. It must descend from an experiment.

Results remain scoped to the recorded protocol and validity domain.

### OAKTransition

Records a status transition and its cause. Promotion to `DEMONSTRATED`, `MEASURED`, `CANONICAL`, or a certified status requires a result ancestor.

A transition event records governance; it does not create scientific truth.

### MMinusRule

Turns a failed result or refutation into reusable negative memory:

- failure context;
- prohibited inference;
- reusable constraint;
- next discriminating test.

M⁻ cannot be created without a failed `ResultPacket` or a `REFUTED` transition ancestor.

### ActionProposal

Records the next reversible draft, simulation, benchmark, documentation task, or human-approved action. It must descend from OAK or M⁻.

An autonomous action must be reversible and explicitly approved. R0.1 does not execute physical instruments, publish externally, spend money, file IP, or perform irreversible actions.

## 4. Structural gates

The append-only ledger rejects:

```text
ClaimEvent without ObservationEvent ancestry
GeneratorCandidate without ClaimEvent ancestry
ExperimentSpec without GeneratorCandidate ancestry
ResultPacket without ExperimentSpec ancestry
promoted OAKTransition without ResultPacket ancestry
MMinusRule without failed result or refutation
ActionProposal without OAKTransition or MMinusRule ancestry
cross-subject parenting without explicit cross_subject flag
out-of-order timestamps
unknown parents
duplicate IDs
hash mismatches
unsafe autonomous actions
```

## 5. Bridges

### HyperKnowledge → Discovery Kernel

`claim_events_from_cell(...)` converts each `ClaimAtom` in a `KnowledgeCell` into a `ClaimEvent`, preserving scope, assumptions, failure conditions, and provenance.

### Generator Stack → Discovery Kernel

`generator_event_from_morph_ir(...)` converts `MorphIR` into a `GeneratorCandidate` while preserving continuous, discrete, and singular sectors, invariants, residual, and uncertainty.

### Discovery Kernel → HyperKnowledge

`result_event_to_evidence_record(...)` converts a `ResultPacket` into a typed HyperKnowledge `EvidenceRecord`:

- successful results become `result` evidence;
- failed results become `counterexample` evidence;
- event hash, units, uncertainty, baseline, and protocol remain attached.

This creates the first executable round trip:

```text
KnowledgeCell
→ ClaimEvent
→ MorphIR generator
→ experiment
→ result
→ EvidenceRecord
→ updated KnowledgeCell
```

## 6. Raman demonstration

The checked-in demo models a synthetic temperature-induced Raman transformation.

The initial claim proposes a shift-plus-broadening generator. A held-out experiment is declared with an independently fitted Lorentzian baseline and a preregistered normalized spectral RMSE threshold.

The candidate fails:

```text
candidate RMSE: 0.031
threshold:      0.020
baseline RMSE:  0.018
```

The system then records:

```text
SIMULATED → REFUTED
```

and creates an M⁻ rule forbidding the inference that shift plus broadening alone is a reusable physical explanation. The next action adds baseline drift as a competing generator under matched cross-validation.

The failure is intentional: the demo verifies that the architecture can preserve a negative result, narrow the claim, and route the next experiment instead of hiding the failure.

## 7. Outputs

```text
manifest.json
ledger.json
events.jsonl
audit.json
graph.json
report.md
```

Run:

```bash
python -m omega_discovery_kernel_t demo \
  --output-dir generated/omega_discovery_kernel_t/raman-r0-1
```

Audit an existing event stream:

```bash
python -m omega_discovery_kernel_t audit path/to/events.jsonl
```

Or:

```bash
python examples/omega_discovery_kernel_demo.py
```

## 8. Metrics

R0.1 reports:

```text
event count
subject count
closed-loop coverage
failed-result count
negative-memory coverage
provenance coverage
unit coverage for results
uncertainty coverage for results
```

These are workflow and traceability metrics, not truth probabilities.

## 9. OAK falsification criteria for the kernel

The program should be reduced or redesigned if:

- it cannot exchange objects with HyperKnowledge and Generator Discovery without manual rewriting;
- hash and parent checks fail to detect altered or orphaned events;
- failed results do not reliably produce M⁻ constraints;
- the event layer adds more complexity than it removes;
- external researchers cannot reproduce a closed-loop bundle;
- event completeness becomes a proxy for scientific correctness;
- unsafe or irreversible actions can bypass approval gates;
- real benchmark performance is not improved over simpler workflows.

## 10. R0.2 priorities

1. Stable universal IDs linking R0.2 theory nodes, R0.3 knowledge cells, claims, MorphIR, experiments, results, commits, and datasets.
2. Content-addressed source locators and exact line/page/range provenance.
3. JSON Schema validation in CI for every event stream.
4. Unit-aware quantity objects and calibrated uncertainty distributions.
5. Automatic propagation of `ResultPacket` into versioned `KnowledgeCell` updates.
6. Stale-status detection when new evidence contradicts a promoted claim.
7. Independent baseline and replication fields.
8. Event streaming and checkpointing through Ω-SANS-PLAFOND-T∞.
9. Git commit and CI events as epistemic transitions.
10. A real Raman/FTIR benchmark with held-out spectra and nonlinear least-squares baselines.

## 11. Boundary

Ω-DISCOVERY-KERNEL-T∞ R0.1 is infrastructure for traceable scientific reasoning and workflow governance.

It is not:

- proof of a new physical law;
- a replacement for domain experts;
- permission to operate instruments autonomously;
- a guarantee of scientific novelty;
- evidence of patentability;
- evidence of revenue or product-market fit.

Its value must be demonstrated by reduced audit time, better reproducibility, fewer repeated failures, stronger experiment selection, or improved out-of-sample scientific performance against external baselines.
