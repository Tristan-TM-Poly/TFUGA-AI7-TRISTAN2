# Ω-NARUTO-HMAGFM-HGFMnD² — R1.2

**Status:** exploratory architecture + executable OAK software scaffold.  
**Boundary:** Naruto and Naruto Shippuden provide design metaphors. No fictional mechanism is asserted to exist physically.

## Purpose

R1.2 converts narrative operators into bounded engineering objects:

- chakra → compute, memory, energy, time, attention, and human-review budgets;
- Kage Bunshin → isolated parallel proposals with evidence and provenance;
- Byakugan → observability through deterministic graph export;
- Genjutsu → adversarial checks for fabricated, circular, private, or inflated claims;
- seals → PrivacyGate, IPGate, SafetyGate, maturity, evidence, and human-review requirements;
- M⁻ → retained rejected conclusions and their failure reasons.

## Core pipeline

```text
hypothesis
→ bounded clone proposals
→ evidence/provenance/risk checks
→ OAKMerge ranking
→ contradictions + M⁻
→ publication gates
→ HGFMnD² JSON/GraphML
→ robustness scenarios
→ reviewable report
```

Selection is not certification. A high local score is not proof, institutional approval, or authorization to publish.

## Epistemic ladder

```text
F0 fiction/metaphor
I1 intuition
H2 falsifiable hypothesis
D3 formal definition
S4 simulation
P5 prototype
B6 reproducible benchmark
E7 experimental evidence
R8 independent replication
C9 domain-bounded canon
```

## OAKMerge

`oak_merge` rejects or retains proposals when they:

- exceed the available `ChakraBudget`;
- cross privacy, IP, or safety thresholds;
- lack evidence or provenance.

Supported candidates are ranked deterministically. Contradictions are preserved instead of erased, and rejected proposals remain available as falsification memory.

## Genjutsu audit

The deterministic red-team layer flags:

- fabricated or placeholder source markers;
- circular evidence;
- private or restricted source markers;
- benchmark-or-higher status with insufficient artifacts;
- missing provenance;
- confidence/uncertainty mismatch.

These rules are adversarial lint, not a universal deception detector.

## Baseline benchmark

The included fixture compares:

1. evidence-aware `OAKMerge`;
2. majority vote;
3. highest self-reported confidence.

Two unsupported clones agree with each other while one documented minority clone disagrees. OAKMerge selects the documented result on this fixture. That is a reproducible software result, not evidence of universal superiority.

## HGFMnD² export

`build_hgfmn_graph` emits deterministic JSON and GraphML nodes/edges for:

- hypotheses;
- proposals;
- evidence;
- provenance;
- local selection;
- contradictions;
- M⁻ retention.

Graph presence does not validate a node's truth.

## Robustness analysis

R1.2 perturbs confidence, uncertainty, evidence, rivals, and risk. The default fixture intentionally exposes one instability: once the selected proposal crosses the risk gate, no proposal remains acceptable.

Robustness is a sensitivity diagnostic, not scientific truth or global optimality.

## Run

```bash
omega-naruto-oak
omega-naruto-oak \
  --output generated/omega_naruto/report.json \
  --graphml-output generated/omega_naruto/graph.graphml

python -m pytest -q tests/test_omega_naruto*.py
```

## CI

The dedicated workflow runs on Python 3.10, 3.11, and 3.12. It:

- compiles the package and tests;
- runs 21 focused tests;
- parses four JSON Schemas;
- validates the R1.2 report and graph against JSON Schema;
- parses GraphML;
- uploads a deterministic report artifact on Python 3.11.

## Non-claims

This module does not claim:

- chakra or jutsu as physical fields or mechanisms;
- free energy, zero dissipation, or negative-infinite entropy;
- autonomous scientific certification;
- universal superiority of OAKMerge;
- permission to expose private or patent-sensitive information;
- replacement of experts or human judgment.

## Next OAK gates

- larger benchmark corpus with preregistered expected outcomes;
- score-weight calibration and ablation studies;
- optional semantic contradiction detector with audit trail;
- integration with a reviewed ClaimTransmuter contract;
- independent reproduction outside the repository.
