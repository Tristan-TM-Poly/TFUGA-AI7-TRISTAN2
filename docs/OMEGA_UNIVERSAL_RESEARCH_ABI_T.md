# Ω-UNIVERSAL-RESEARCH-ABI-T∞ — R0.1

## Mission

Crystallize the smallest shared typed substrate that lets Tristan systems compose **without collapsing their ontologies**.

This PR is stacked on Ω-GITHUB-CUMULATIVE-MEMORY-T∞ (#447), itself stacked on Ω-CAPABILITY-OS-T∞ (#417). It reuses Capability OS natively and exposes explicit snapshot bridges for the independent open stacks GreatSages/Tensor Research (#443), Discovery OS (#444), Compute Physics / Optimization Foundry (#445), and Cognitive Computer (#446).

The central invariant is:

```text
reuse existing ontology
→ translate through a typed boundary
→ preserve provenance + uncertainty + authority + OAK state
→ transform
→ emit a receipt
→ validate
→ only then crystallize/promote
```

## 1. Six graphs, not one universal soup

The ABI keeps six logically distinct graphs:

```text
G_K Knowledge   = Claim / Evidence / Assumption / Theory / Representation
G_C Capability  = Capability / Skill / Module / Tool / Adapter
G_W Work        = Intent / WorkUnit / Dependency / Schedule / Budget
G_E Experiment  = Hypothesis / Intervention / Observation / Residual / Benchmark
G_P Provenance  = Artifact / Commit / Event / Receipt / Lineage
G_V Value       = Cost / Risk / Utility / Option / Revenue / IP / Human effort
```

Cross-graph edges are typed references. The architecture explicitly refuses:

```text
claim == evidence
capability == authority
work == validation
experiment == causal proof
provenance == truth
value == scientific validity
```

## 2. Universal envelope

Every imported object receives a bounded envelope with:

```text
ObjectRef
schema_version
content_hash
graph
object_type
object_id
payload
provenance[]
uncertainty
authority
OAK state
valid_time
known_time
```

The content hash is deterministic canonical JSON. This is an interoperability checksum, not a semantic-equivalence proof.

## 3. No Important Transformation Without Receipt

Every meaningful transformation may emit:

```text
TransformationReceipt =
  operator
  inputs[]
  outputs[]
  assumptions[]
  invariants[]
  evidence_refs[]
  residuals[]
  uncertainty
  cost
  authority
  risk
  rollback / irreversibility statement
  provenance[]
  OAK state
  fingerprint
```

Hard gates in R0.1:

- OAK `PASS` cannot coexist with a declared non-PASS invariant;
- write/irreversible receipts require an explicit rollback or irreversibility statement;
- causal graph edges require explicit evidence references;
- uncertainty and risk are bounded to `[0,1]`;
- graph endpoints and evidence refs must resolve.

A receipt proves only that the declared ABI contract is internally coherent. It is **not** an external theorem, causal, safety, financial or truth certificate.

## 4. Reuse-before-create integration

R0.1 does not invent a second capability model. `adapt_capability()` consumes the existing `omega_capability_os_t.core.Capability` from #417/#447 and stores its genome inside `G_C` with source ontology retained.

This means the upstream decision remains:

```text
REUSE | COMPOSE | EXTEND | INSPECT | CREATE
```

and the ABI receives only the selected/residual work rather than bypassing `ReuseBeforeCreateGate`.

## 5. Independent PR bridges

Because #443, #444, #445 and #446 are independent open branches, R0.1 deliberately avoids copying their implementations or pretending they are already co-resident. `adapt_snapshot()` creates a narrow bridge with the permanent boundary:

```text
snapshot_bridge != semantic_equivalence_or_external_validation
```

After those stacks merge or are intentionally stacked together, dedicated adapters can replace snapshots one ontology at a time.

## 6. Research state

The global executable state can now be represented as:

```text
S_t = (K_t, C_t, W_t, E_t, P_t, V_t, R_t)
```

where `R_t` is the append-only set of transformation receipts.

A transition is:

```text
S_(t+1) = T_a(S_t) + Receipt(T_a)
```

The research runtime therefore gains an auditable transition algebra rather than only mutable Python objects.

## 7. Bounded LLMT context

`ResearchGraphKernel.context_packet()` keeps the global state external and exposes only top deterministic references per graph. Payloads remain outside the bounded packet by default.

This directly composes with the Zoom/Dézoom doctrine of #447:

```text
global memory
→ rank
→ zoom selected objects
→ compile bounded context
→ act
→ receipt
→ memory
```

## 8. New convergence enabled by the ABI

The shared object model makes several previously separate ideas composable:

```text
GitHub Memory candidate
→ Capability ref
→ WorkUnit
→ Cognitive program snapshot
→ Discovery claim snapshot
→ Experiment / benchmark
→ Compute-cost observation
→ Value record
→ Git commit / artifact provenance
→ Transformation Receipt
```

This is the first executable seed of the broader Epistemic Compute Stack without requiring a monolithic mega-package.

## 9. OAK boundaries

R0.1 does not claim:

- that six graphs are a unique or optimal ontology;
- semantic equivalence across independent systems;
- external truth from hashes or receipts;
- automatic causal inference;
- safe autonomous authority;
- guaranteed research productivity;
- value scores as scientific validity;
- merged PR state as M+;
- snapshot import as validation;
- complete integration of #443–#446 before their code is intentionally co-resident.

## 10. Deterministic court

```bash
python -m compileall -q omega_research_abi_t
pytest -q tests/test_omega_research_abi_t.py
python -m omega_research_abi_t examples/research_abi_fixture.json --compact
```

The fixture instantiates one object in each graph, cross-links them, emits a receipt, validates graph integrity and compiles a bounded context packet.

## 11. Next residual generations

Only after R0.1 exact-head CI:

1. dedicated Discovery OS adapter for `ClaimCertificate`, `ScientificBuildGraph` and theory diff;
2. Cognitive Computer adapter for CIR/instruction/program/obligation refs;
3. Compute Physics adapter for Snapshot, Complexity-IR, OptimizationGene and BenchmarkContract;
4. GreatSages adapter for DiscoveryPath, representation morphism and TensorResearch coalition receipts;
5. typed `TheoryDiffReceipt` and `RepresentationTransportReceipt`;
6. M+/M-/M? learning over reuse and transformation outcomes;
7. receipt-addressed scientific bisect;
8. Value-of-Information scheduling over Confidence Debt;
9. six-graph query planner for LLMT/agent context compilation;
10. verified promotion handoff to OAKGate / Asset Factory only after external gates.

Operating law:

```text
NO IMPORTANT TRANSFORMATION WITHOUT RECEIPT
NO NEW ONTOLOGY WHEN AN EXISTING ONE CAN BE ADAPTED
NO CROSS-SYSTEM EQUIVALENCE WITHOUT EVIDENCE
NO VALUE OPTIMIZATION BEFORE HARD OAK/AUTHORITY GATES
PLUS ULTRA = MORE COMPOSITION + MORE PROOF + LESS DUPLICATION
```
