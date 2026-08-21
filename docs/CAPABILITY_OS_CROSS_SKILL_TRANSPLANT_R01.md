# Ω-CAPABILITY-OS Cross-Skill Transplant R0.1

## Mission

Compile the verified R0.4→R0.10 meta-theory courts into the already-canonical `omega_capability_os_t` instead of creating a second capability ontology.

```text
existing Capability OS Capability
→ finite SkillContext interfaces
→ input/output contract checks
→ authority non-widening gate
→ independent frozen provenance slices
→ cross-run reproducibility
→ historical replay
→ counterfactual replay
→ PROMOTE | HOLD
```

## Reuse-first decision

The repository already contains a canonical Capability OS with Capability Genome, consumes/produces contracts, authority lattice, planning, evidence receipts and M+/M−. Historical Research ABI / Transformation Receipt layers also exist. Therefore R0.1 adds only a transplant adapter.

```text
NewCapabilityOntology = rejected
ExistingCapabilityOS + TransplantAdapter = selected
```

## Cross-skill rule

A capability may be transplanted only when every declared target context can consume its declared inputs, receive required outputs, and do so without increasing authority.

```text
CanTransfer != MayWidenAuthority
InterfaceMatch != SemanticEquivalence
MultiSkillPASS != UniversalCapability
```

R0.1 intentionally uses synthetic finite contexts in the court (`github`, `research`, `document`). These prove software behavior only; they do not prove actual product/tool effectiveness in those external systems.

## R0.10 inheritance

Promotion also requires the existing R0.10 courts:

- provenance independence over declared frozen slices;
- exact cross-run decision reproducibility;
- historical replay without unapproved regressions;
- counterfactual candidate-vs-baseline replay.

The adapter imports these contracts directly from `omega_generative_closure_t.reprovenance_replay`.

## OAK boundaries

```text
CapabilityGenome != ExecutedCapability
ContractCoverage != BehavioralCompatibility
ProvenanceDisjoint != StatisticalIndependence
ReproducibleDecision != CorrectDecision
HistoricalReplayPASS != HistoricalOptimality
CounterfactualReplayPASS != RealWorldCausalBenefit
PROMOTE != ExternalActionAuthority
CI green != ExternalWorldTruth
```

## Saturation / next action

This is a transplantation test, not R0.11. If the adapter survives exact-head CI, the next valuable work is empirical adapters for real skill traces only where evidence exists. No generic layer should be added merely because another version number is available.
