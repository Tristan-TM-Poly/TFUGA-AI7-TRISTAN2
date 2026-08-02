# Ω-NARUTO-HMAGFM-HGFMnD² — R1.1

**Status:** exploratory architecture + executable OAK scaffold.  
**Scientific boundary:** Naruto and Naruto Shippuden are used as design metaphors. No fictional mechanism is claimed to exist physically.

## Purpose

This branch converts narrative operators into testable engineering objects:

- chakra -> bounded compute, memory, energy, time and human-review budgets;
- Kage Bunshin -> parallel agents with isolated hypotheses and merged evidence;
- Rasengan -> constrained vortex/control optimization;
- Byakugan -> observability and system instrumentation;
- Sharingan -> pattern transfer with provenance and domain limits;
- Sage Mode -> internal/external sensor fusion;
- seals -> permissions, consent and irreversible-action gates;
- Genjutsu -> adversarial information and hallucination testing;
- Bijuu -> high-capability modules requiring containment and audit;
- villages -> federated specialist laboratories;
- Hokage -> accountable human governance, not absolute authority.

## Core coupling

HGFMnD² is the dynamic second-order hypergraph:

```text
G_t = (V_t, E1_t, E2_t, X_t, U_t, P_t, R_t)
```

where `U` is uncertainty, `P` provenance/evidence, and `R` residues, contradictions and negative memory.

HMAGFM² is the agent layer. Each agent proposes a transformation:

```text
proposal_i = agent_i(G_t, budget_i, constraints_i, specialization_i)
G_(t+1) = OAKMerge(G_t, proposals)
```

No single agent may write directly to the canon.

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

A proposal cannot skip evidence states. Names are callable labels, not proofs.

## Chakra budget

A chakra budget is a non-negative resource vector:

```text
C = (compute, memory, energy, time, attention, human_review)
```

A valid execution must fit within the available budget. The target is not maximum consumption but maximum verified value per unit of resource.

## Kage Bunshin protocol

Each clone-agent receives:

1. one explicit hypothesis;
2. one bounded budget;
3. one isolated execution context;
4. one falsification target;
5. one required evidence report;
6. one uncertainty estimate;
7. one residue report.

`OAKMerge` then:

1. rejects malformed or unsupported proposals;
2. preserves contradictions;
3. selects the strongest supported candidate;
4. archives rejected candidates in M-minus;
5. proposes a discriminating next experiment when evidence conflicts.

## Publication gate

```text
Publish = ConsentGate -> PrivacyGate -> IPGate -> EvidenceGate -> SafetyGate
```

R1.1 makes these gates explicit through `GatePolicy` and `GateReport`.
A technically strong proposal may still be blocked or remain in `WARN` until human review is completed.

Blocked examples:

- private identity data not required by the artifact;
- claims of physical proof based on analogy;
- automatic publication of patent-sensitive material;
- irreversible actions without explicit authorization;
- claims stronger than the attached evidence.

## Genjutsu red team

The deterministic Genjutsu audit searches for:

- fabricated or placeholder source markers;
- circular evidence where the conclusion is its own proof;
- private or restricted source markers;
- benchmark-or-higher status without enough evidence;
- missing provenance;
- confidence that conflicts with stated uncertainty.

These checks are adversarial lint, not a scientific validator.

## Baseline benchmark

R1.1 compares three selection strategies:

1. `OAKMerge`: evidence-aware and provenance-aware;
2. majority vote: counts conclusions but ignores proof quality;
3. highest confidence: trusts self-reported confidence.

The included hype fixture contains two unsupported clones agreeing with each other and one documented minority clone. Majority vote and highest-confidence selection fail the fixture; OAKMerge selects the documented result.

This is a deterministic software test, not evidence that OAKMerge dominates every possible aggregation method.

## Repository integration

R1.1 adds:

- JSON Schema for agent proposals;
- JSON Schema for merge results;
- conservative claim-packet export;
- M-minus-compatible rejection packets;
- a dependency-light integration boundary;
- the `omega-naruto-oak` command-line report.

Run:

```bash
omega-naruto-oak
omega-naruto-oak --output generated/omega_naruto/report.json
```

The report includes:

- accepted local proposal;
- ranking and contradictions;
- publication-gate status;
- Genjutsu findings;
- baseline comparison;
- retained M-minus residues;
- an explicit non-claim boundary.

## OAK claim ledger

| Claim | Status | Required test | Failure mode |
|---|---|---|---|
| Parallel agents can explore distinct hypotheses | D3 | deterministic unit test | duplicate agents masquerade as diversity |
| OAKMerge can rank evidence-bearing proposals | P5 | adversarial proposal set | score hides missing provenance |
| Contradictions can be preserved instead of erased | P5 | conflicting-clone test | majority vote suppresses minority evidence |
| A resource budget can block over-allocation | P5 | exhaustion test | negative or non-finite resource values |
| Publication gates can separate ranking from release | P5 | privacy/IP/safety fixtures | automatic pass mistaken for authorization |
| Genjutsu audit can flag known deception patterns | P5 | deterministic adversarial fixtures | heuristic lint mistaken for universal detection |
| OAKMerge can outperform naive baselines on the hype fixture | B6-local | fixed reproducible fixture | fixture-specific success generalized universally |
| Naruto metaphors improve engineering communication | H2 | user study / task benchmark | memorable language mistaken for science |

## Non-claims

This module does not claim:

- chakra as a physical field;
- fictional techniques as real mechanisms;
- zero dissipation, free energy or negative infinite entropy;
- autonomous scientific certification;
- universal superiority of OAKMerge;
- institutional approval;
- replacement of expert or human judgment.

## Next gates

1. Add HGFMnD² graph export for proposals, evidence and contradictions.
2. Add semantic contradiction detection behind an optional, audited interface.
3. Add calibration and sensitivity analysis for proposal-score weights.
4. Add property-based tests for ordering, duplicate IDs and risk thresholds.
5. Connect claim packets to a reviewed ClaimTransmuter contract.
6. Add a reproducible benchmark corpus larger than the single hype fixture.
