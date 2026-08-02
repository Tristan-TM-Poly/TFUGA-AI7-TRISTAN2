# Ω-NARUTO-HMAGFM-HGFMnD² — R1.0

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

Blocked examples:

- private identity data not required by the artifact;
- claims of physical proof based on analogy;
- automatic publication of patent-sensitive material;
- irreversible actions without explicit authorization;
- claims stronger than the attached evidence.

## First executable artifact

The first implementation contains:

- `ClaimStatus` and `AgentProposal` types;
- `ChakraBudget` validation;
- deterministic `oak_merge` ranking;
- contradiction and negative-memory preservation;
- a next-experiment recommendation;
- unit tests with three contradictory clone proposals.

## Initial OAK claim ledger

| Claim | Status | Required test | Failure mode |
|---|---|---|---|
| Parallel agents can explore distinct hypotheses | D3 | deterministic unit test | duplicate agents masquerade as diversity |
| OAKMerge can rank evidence-bearing proposals | P5 | adversarial proposal set | score hides missing provenance |
| Contradictions can be preserved instead of erased | P5 | conflicting-clone test | majority vote suppresses minority evidence |
| A resource budget can block over-allocation | P5 | exhaustion test | negative or non-finite resource values |
| Naruto metaphors improve engineering communication | H2 | user study / task benchmark | memorable language mistaken for science |

## Non-claims

This module does not claim:

- chakra as a physical field;
- fictional techniques as real mechanisms;
- zero dissipation, free energy or negative infinite entropy;
- autonomous scientific certification;
- institutional approval;
- replacement of expert or human judgment.

## Next gates

1. Add JSON schema for proposals and evidence.
2. Add graph export for HGFMnD² state.
3. Add Genjutsu adversarial fixtures.
4. Add Privacy/IP/Safety gate tests.
5. Benchmark OAKMerge against majority vote and naive score averaging.
6. Connect accepted proposals to the repository ClaimTransmuter and M-minus registry.
