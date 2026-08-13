# Ω-TENSOR-RESEARCH-COMPILER-T∞ — R0.6

## Status

**Executable software architecture / benchmark contract.**

R0.6 fuses the GreatSages research compiler with logical per-person LLMT profiles,
ephemeral Shadow projections, sparse tensor coalition routing, a typed Cognitive
ISA, the R0.5 representation gate and the R0.4 DiscoveryPath runtime trace.

It does **not** claim that a PersonLLMT is a person, that a Shadow reproduces a
mind, that consensus proves truth, that a tensor score proves causal synergy, or
that the greedy router finds the global optimum.

## Mother architecture

```text
Problem
  -> ProblemGenome
  -> PersonLLMT Registry
  -> Sparse Tensor Coalition Router
  -> Shadow Factory
  -> Typed Cognitive Program
  -> R0.5 Representation / Noether gates
  -> R0.4 DiscoveryPath trace
  -> CVCD/DIFF-style tensor merge
  -> OAK / evidence / residuals
```

The governing optimization objective is:

```text
smallest useful coalition
+ verified coverage
+ complementary operators
- redundancy
- cost
- risk
- epistemic debt
```

This is GO MAX applied to model selection and research-program compilation.

## R0.6A — PersonLLMT Registry

A `PersonLLMT` is a logical, source-aware software profile:

```text
PersonLLMT
  person_id
  model_version
  corpus_ids
  source_ids
  operator_ids
  representation_ids
  capability_tags
  temporal_gate_year
  permission_scope
  cost
  risk
  epistemic_debt
  model_not_person = true
  historical_mind_certified = false
```

A logical profile may share a foundation model with many other profiles. R0.6
does not require one independently trained parameter set per person.

The permanent distinction is:

```text
PersonLLMT != person
software profile != consciousness
style similarity != cognitive reconstruction
```

The Gauss bridge derives its operator/source surface from the existing
GreatSages profile and preserves `model_not_person=True`.

## R0.6B — Shadow Factory

A Shadow is an ephemeral functional projection:

```text
Shadow(person, role, domain, temporal_gate, mirror, operators,
       representations, objective)
```

R0.6 supports solver, critic, formalizer, counterexample, representation and
evidence roles plus historical, modern, computational, adversarial and formal
mirrors.

Every Shadow is:

```text
ephemeral = true
model_not_person = true
```

Private-data Shadows fail closed unless the PersonLLMT permission scope is
`consented_private`.

Technical access to a corpus is never treated as consent to impersonate or
construct a private clone.

## R0.6C — Sparse Tensor Coalition Compiler

Conceptually the Shadow space can be viewed as a product over person, role,
domain, time, mirror, operator, representation and objective. R0.6 deliberately
does **not** materialize that full Cartesian/tensor space.

Instead it performs sparse greedy routing. At each step it computes a declared
marginal score using:

- newly covered required capabilities;
- evidence strength proxy;
- diversity/complementarity;
- redundancy;
- cost;
- risk;
- epistemic debt.

A candidate is added only while its marginal gain exceeds a threshold and the
risk budget is satisfied.

This is a bounded heuristic:

```text
greedy_heuristic_not_global_optimum = true
full_tensor_materialized = false
```

The deterministic CI fixture uses three **synthetic** people. `person_a` and
`person_b` cover complementary capabilities and are selected. `person_c` is
redundant and more expensive, so it is rejected. The fixture exists to test the
router; it makes no historical claim.

## R0.6D — Typed Cognitive ISA

The instruction vocabulary includes:

```text
LOAD GATE ZOOM DEZOOM REP CVCD INV SYM APPROX RESIDUAL
TRANSFER BRANCH COUNTER MERGE SIM PROVE OAK STORE_PLUS STORE_MINUS
```

Each instruction declares input/output types. The first executable chain used
in CI is deliberately small:

```text
PROBLEM
  -- LOAD --> PROBLEM
  -- GATE --> PROBLEM
  -- REP --> REPRESENTATION
  -- APPROX --> REPRESENTATION
  -- INV --> CLAIM
  -- OAK --> OAK_RECEIPT
  -- STORE_PLUS --> ARTIFACT
```

A syntactically plausible but type-incompatible sequence is quarantined.

This provides **cognitive type safety as a software contract**. It is not a
claim that human cognition follows this machine model.

## R0.6E — Representation backend

Any instruction that changes its declared representation must be backed by an
R0.5 `RepresentationMorphismR05`.

The program audit fails closed when:

- no matching R0.5 morphism exists; or
- all matching morphisms are quarantined.

Therefore a cognitive program cannot simply assert that a representation
change is useful.

```text
Cognitive instruction
  -> declared representation change
  -> R0.5 morphism
  -> invariant/loss/residual audit
  -> admissible or quarantine
```

## R0.6F — Program vs execution trace

R0.6 keeps two objects separate:

```text
CognitiveProgram = planned program
DiscoveryPath    = modeled runtime trace
```

The deterministic Ceres bridge requires the three operator-bearing program
instructions to match the existing R0.4 path trace exactly:

```text
representation_switch
approximation_residual
invariant_search
```

The bridge receipt always states:

```text
program_is_execution_trace = false
discovery_path_is_runtime_trace = true
```

A successful trace match does not prove the unique historical cognitive path of
Gauss.

## R0.6G — Tensor merge

Shadow outputs are merged by preserving both common and divergent claims.

```text
consensus core = intersection of encoded claim ids
divergence     = per-Shadow claims outside the consensus core
```

Evidence ids are deduplicated, but independence is **not inferred** merely
because multiple Shadows produced the same claim.

Permanent rules:

```text
consensus != truth
multiple Shadows on one source != multiple independent proofs
DIFF is preserved, not erased by majority vote
```

## R0.6H — Synergy receipts

For bookkeeping the current pairwise synthetic synergy proxy is:

```text
Syn(A,B) = Q(A,B) - Q(A) - Q(B) + Q(empty)
```

The receipt always carries:

```text
causal_synergy_proven = false
```

A positive value is a candidate interaction that requires controlled ablation or
benchmark evidence before causal interpretation.

## GO MAX integration

R0.6 implements the first bounded version of:

```text
GO_MAX_TENSOR(problem)
  -> add the candidate with highest positive marginal gain
  -> update covered capabilities and redundancy
  -> stop when coverage is sufficient, budget is exhausted,
     risk blocks the remaining candidates, or marginal gain is too small
```

The intended future objective is verified frontier expansion per resource, not
agent count.

## OAK negative memory

R0.6 canonizes the following M- rules:

```text
M-LLMT1   PersonLLMT != person.
M-SHADOW1 Shadow != mind; Shadows are ephemeral projections.
M-TENSOR1 tensor size != intelligence.
M-TENSOR2 full tensor expansion is computational debt by default.
M-ROUTE1  greedy routing != proof of global optimum.
M-CONS1   consensus != truth.
M-CONS2   shared provenance != independent evidence.
M-SYN1    apparent synergy != causal synergy.
M-PRIV1   technical data access != consent to build a private clone.
M-ISA1    more operators != better research.
M-ISA2    one successful program != causal operator effectiveness.
```

## R0.6 acceptance gates

R0.6 is promotable as a software architecture only if:

1. Python 3.10–3.13 compile and targeted tests pass;
2. PersonLLMT refuses historical-mind certification;
3. private Shadows require explicit consent scope;
4. unsupported Shadow operators fail closed;
5. sparse routing selects the minimal synthetic complementary coalition;
6. risk budgets can leave capabilities explicitly uncovered;
7. bad Cognitive ISA type transitions quarantine the program;
8. missing R0.5 morphisms quarantine representation-changing programs;
9. the Ceres program/operator trace matches the R0.4 fixture;
10. tensor merge preserves consensus and differences without truth promotion;
11. synergy receipts never claim causal proof;
12. schema enums and dataclass fields remain aligned;
13. the report states that no full tensor expansion or global optimum is claimed.

## What comes next

R0.6 should be benchmarked before further agent proliferation.

The next candidate layer is:

```text
R0.7 Tensor DiscoveryBench
  -> compare single PersonLLMT
  -> single Shadow
  -> coalition
  -> cognitive program
  -> Meta routing policy
  -> ablations / contamination tensor / held-out tasks
```

Only after repeated benchmark episodes should R0.8 learn routing/operator credit
and synergy policies.

## Permanent doctrine

```text
MetaLLMT does not maximize the number of simulated minds.
It compiles the smallest sparse coalition that maximizes verified gain.

program != execution
consensus != truth
synergy != causal proof
proxy != natural law
plus ultra = more proved, not more modules
```
