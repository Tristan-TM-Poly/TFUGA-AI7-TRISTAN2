# Ω-GITHUB-CUMULATIVE-MEMORY-T∞ — R0.3 → R0.7

## Mission

Extend R0.1/R0.2 from retrieval + progressive AST zoom into a bounded cumulative learning/federation layer without creating a second capability ontology.

```text
all PR metadata
→ ReuseBeforeCreateGate
→ top-k progressive Zoom
→ changed files + static symbols
→ R0.3 temporal supersession candidates
→ R0.4 residual artifact contract
→ exact-head tests/OAK
→ R0.5 evidence-bearing reuse outcomes
→ R0.6 cross-repository capability contracts
→ R0.7 bounded LLMT federation
→ next request
```

The governing rule remains:

```text
new implementation := requested capability − verified reusable capability
```

## R0.3 — Temporal Supersession Miner

`TemporalSupersessionMiner` compares PRs inside the same repository using temporal order, lexical overlap and changed-file overlap.

It emits **review-only candidates**.

```text
candidate temporal successor != supersedes edge
```

No inferred candidate is inserted as `supersedes` or `replaces`. Strong lineage still requires explicit PR metadata such as:

```text
supersedes: #123
replaces: #123
```

This prevents a newer, similarly named PR from silently erasing history.

## R0.4 — Residual Code Compiler

`ResidualCodeCompiler` compiles an implementation contract rather than hallucinating a complete source tree.

Decision semantics:

| Decision | Generation scope |
|---|---|
| `REUSE` | integration/tests only; duplicate implementation blocked |
| `COMPOSE` | integration/tests only; duplicate implementation blocked |
| `EXTEND` | `residual_outputs` only |
| `INSPECT` | blocked pending exact source/diff inspection |
| `CREATE` | requested capability only after retrieval exhaustion |

Every residual artifact spec contains selected capabilities, missing outputs, exact inspection refs, required tests, provenance and an explicit generation boundary.

```text
generation_allowed != permission to mutate GitHub
```

## R0.5 — Reuse Outcome Learning

`ReuseOutcomeReceipt` requires explicit evidence references and keeps:

```text
SUCCESS  → M+
FAILURE  → M-
DEGRADED → M?
```

A merge event is never accepted as the outcome itself.

The learner records empirical utility for reuse actions and selected capabilities using success/failure/degraded counts plus bounded deltas for defects, complexity, latency and maintenance.

These statistics are policy evidence, not causal proof. Small samples cannot override current OAK checks.

## R0.6 — Cross-Repository Capability Graph

`CrossRepositoryCapabilityGraph` joins multiple repository memories by capability contract while preserving provenance.

Two cases stay distinct:

```text
same capability ID + same contract signature
→ shared-contract candidate

same capability ID + different contract signature
→ explicit conflict receipt
```

No observation is silently overwritten.

```text
matching contract != same implementation
contract conflict != proof that one implementation is superior
```

This is designed to connect later with Ω-MASTER-DOC-ATLAS-T∞ receipts rather than replacing them.

## R0.7 — LLMT Federation

`LLMTFederationCompiler` creates logical context identities with scopes:

```text
global
pr
module
```

Each packet is a bounded projection of the same canonical GitHub memory and retains the global context fingerprint.

Authority is intentionally capped at:

```text
read | draft
```

A specialized packet cannot escalate itself to `write` or `irreversible`.

Multiple LLMT identities are not modeled as independent people, minds or independent evidence sources. They may share one underlying model/runtime.

## Unified deterministic court

`compile_evolution_court()` executes R0.3→R0.7 as one deterministic receipt:

```text
supersession report
+ residual artifact spec
+ reuse policy summary
+ cross-repository graph receipt
+ LLMT federation receipt
+ OAK boundaries
```

The CI workflow runs this after the real read-only GitHub metadata refresh and progressive top-k AST hydration.

## CLI

```bash
python -m omega_capability_os_t.github_memory_evolution_cli supersession MEMORY.json

python -m omega_capability_os_t.github_memory_evolution_cli residual \
  MEMORY.json REQUEST.json

python -m omega_capability_os_t.github_memory_evolution_cli learn-outcomes \
  OUTCOMES.json

python -m omega_capability_os_t.github_memory_evolution_cli cross-repo \
  REPO_A.json REPO_B.json \
  --repository owner/a --repository owner/b

python -m omega_capability_os_t.github_memory_evolution_cli federation \
  MEMORY.json REQUEST.json --identities identities.json

python -m omega_capability_os_t.github_memory_evolution_cli court \
  MEMORY.json REQUEST.json \
  --outcomes outcomes.json \
  --identities identities.json
```

## Recursive Capability Genome

R0.3→R0.7 self-registers these reusable capabilities:

```text
github.supersession.mine
github.residual.compile
github.reuse_outcome.learn
github.cross_repo.graph
github.llmt_federation.compile
```

Together with R0.1/R0.2:

```text
github.memory.index
github.capability_graph.compile
github.reuse_before_create
github.llmt_context.compile
github.memory.progressive_zoom
github.symbol.ast.extract
```

A later agent should therefore discover this stack before inventing another memory/reuse/federation architecture.

## OAK boundaries

```text
PR_MERGED != M_PLUS
PR_SIMILARITY != SEMANTIC_EQUIVALENCE
AST_SYMBOL_EXISTS != REUSABLE_BEHAVIOR
INFERRED_SUPERSESSION != STRONG_LINEAGE
GENERATION_ALLOWED != WRITE_AUTHORITY
REUSE_OUTCOME != CAUSAL_PROOF
MATCHING_CAPABILITY_CONTRACT != SHARED_IMPLEMENTATION
LLMT_PACKET_COUNT != INDEPENDENT_EVIDENCE
CI_GREEN != EXTERNAL_WORLD_TRUTH
```

## Next frontier

The next useful frontier is not another parallel memory layer. It is empirical validation on real future PR decisions:

```text
reuse decision
→ implementation choice
→ exact-head CI / benchmarks / maintenance evidence
→ ReuseOutcomeReceipt
→ M+/M-/M?
→ learned policy
→ future decision comparison
```

That loop is what can turn cumulative GitHub memory from a retrieval architecture into a measured engineering advantage.
