# Ω-GITHUB-CUMULATIVE-MEMORY-T∞ — R0.1→R0.2

## Mission

Turn GitHub from a collection of successive PRs into cumulative executable architectural memory.

The invariant is:

```text
new intent
→ retrieve all PR metadata
→ rank existing work
→ progressively zoom into top candidates
→ inspect changed files + static symbols
→ reuse / compose / extend
→ generate only the residual
→ OAK
→ persist lineage
```

The system is deliberately implemented as an extension of Ω-CAPABILITY-OS-T∞ rather than a parallel capability model.

## Reused foundations

R0.1→R0.2 intentionally reuses instead of duplicating:

- **Ω-CAPABILITY-OS-T∞ / PR #417** — `Capability`, Capability Genome, consumes/produces, quality, reuse, cost, risk, authority, health, OAK and M+/M−;
- **Ω-MASTER-DOC-ATLAS-T∞ / PR #414** — cross-repository provenance and structural candidate input through `ingest_master_atlas`; Atlas similarity is never promoted to semantic equivalence;
- **GreatSages Tensor Research Compiler / PR #443** — sparse-selection doctrine: choose the smallest useful set, not the largest agent/module population.

The new code is restricted to the previously missing residual:

1. PR lifecycle/history memory;
2. changed-file / atlas asset observations;
3. typed lineage and supersession graph;
4. `ReuseBeforeCreateGate`;
5. bounded LLMT context packet;
6. read-only live GitHub snapshot adapter;
7. progressive candidate hydration;
8. static Python AST symbol observations.

## Core objects

### `GitHubMemoryIndex`

Stores distinct evidence classes without collapsing them:

```text
formal Capability observations
PR historical records
asset candidates (changed files / atlas candidates / AST symbols)
typed graph edges
```

PR state is preserved as `OPEN`, `DRAFT`, `MERGED`, or `CLOSED`.

**A merged PR is not automatically M+.** Lifecycle is history; M+ requires explicit validated outcome evidence.

### `CapabilityGraph`

Typed relations:

```text
uses
implements
extends
duplicates
replaces
supersedes
conflicts
generalizes
specializes
derived_from
tests
failed_because
candidate_similarity
```

Only explicit PR-body lineage declarations are promoted automatically to strong lineage edges. Lexical similarity remains a candidate signal.

Recommended PR-body lineage syntax:

```text
reuses: PR-417, #414
extends: #417
derived_from: #443
supersedes: #123
```

### `ReuseBeforeCreateGate`

Decision space:

```text
REUSE
COMPOSE
EXTEND
INSPECT
CREATE
```

The gate is fail-closed toward creation:

- exact formal coverage → `REUSE`;
- multiple capabilities cover the request → `COMPOSE`;
- useful partial formal coverage → `EXTEND`, with explicit residual outputs;
- only historical/structural candidates exist → `INSPECT`;
- no meaningful existing candidate → `CREATE`.

`creation_allowed=true` occurs only for the last case.

This implements the Minimal Novelty Principle:

```text
new_code := requested_capability − verified_existing_capability
```

### LLMT Context Compiler

`compile_context()` emits a bounded packet containing:

- the requested capability;
- reuse decision;
- top formal capabilities;
- top historical/asset leads;
- relevant graph relations;
- OAK instructions;
- deterministic fingerprint.

The packet is intended to be small enough for a PR-specialized LLMT while the global index remains external memory.

## R0.2 — Progressive Zoom / Symbol Genome

The global index deliberately stays cheap. It first reads every PR as metadata only, then `ProgressiveGitHubRetriever` hydrates only the highest-ranked historical candidates.

```text
all PR metadata
→ lexical/capability ranking
→ top-k PRs
→ PR detail
→ changed filenames
→ selected Python source at candidate head SHA
→ static AST classes/functions/methods
→ asset observations
→ recompile LLMT context
```

This directly implements a Zoom/Dézoom discipline for model context and API cost.

The AST extractor parses candidate Python source but **does not execute it**. Syntax failures are retained in the retrieval receipt rather than silently promoted.

Every symbol observation carries the boundary:

```text
AST_SYMBOL_EXISTS != REUSABLE_BEHAVIOR
```

Exact implementation and tests remain mandatory before a candidate becomes a reuse decision.

## Live memory

The read-only adapter can refresh from every PR available through the GitHub REST API:

```bash
python -m omega_capability_os_t.github_memory_cli build \
  --repository OWNER/REPO \
  --registry examples/capability_os_registry.json \
  --output /tmp/github-memory.json
```

For cheap passive refreshes, omit per-PR changed-file calls:

```bash
python -m omega_capability_os_t.github_memory_cli build \
  --repository OWNER/REPO \
  --registry examples/capability_os_registry.json \
  --without-files \
  --output /tmp/github-memory.json
```

Then zoom only into top candidates:

```bash
python -m omega_capability_os_t.github_memory_zoom \
  /tmp/github-memory.json \
  examples/github_memory_request.json \
  --top-prs 5 \
  --max-files-per-pr 8 \
  --output-index /tmp/github-memory-zoom.json \
  --output-context /tmp/github-context.json \
  --output-receipt /tmp/github-zoom-receipt.json
```

## Reuse check

Request example:

```json
{
  "request_id": "PR-NEXT",
  "description": "Build a GitHub PR memory and reusable capability graph",
  "domains": ["github", "memory"],
  "consumes": ["repository", "capability_registry"],
  "produces": ["pr_index", "capability_graph"]
}
```

Run:

```bash
python -m omega_capability_os_t.github_memory_cli reuse-check \
  /tmp/github-memory.json \
  examples/github_memory_request.json
```

Or compile LLMT context:

```bash
python -m omega_capability_os_t.github_memory_cli context \
  /tmp/github-memory.json \
  examples/github_memory_request.json
```

## Self-description in Capability OS

The implementation registers its own reusable capabilities:

```text
github.memory.index
github.capability_graph.compile
github.reuse_before_create
github.llmt_context.compile
github.memory.progressive_zoom
github.symbol.ast.extract
```

This matters recursively: later agents can discover and reuse the memory/reuse machinery itself instead of inventing another one.

## Passive operation

The companion workflow is read-only. On PR changes, manual dispatch, and a bounded schedule it:

1. runs the GitHub-memory + progressive-zoom OAK courts;
2. snapshots all PR metadata using `GITHUB_TOKEN` with read permissions;
3. ingests the Capability OS registry;
4. hydrates only the top two live smoke candidates;
5. extracts bounded static Python symbol observations;
6. recompiles the bounded LLMT context;
7. uploads memory/context/zoom receipts as CI artifacts.

It does not merge, comment, mutate PRs, publish IP, or advance a canonical pointer.

## OAK boundaries

```text
PR_MERGED != M_PLUS
PR_SIMILARITY != SEMANTIC_EQUIVALENCE
CHANGED_FILE != REUSABLE_CAPABILITY
AST_SYMBOL_EXISTS != REUSABLE_BEHAVIOR
ATLAS_NAME_MATCH != SHARED_IMPLEMENTATION
CANDIDATE_REUSE != VERIFIED_REUSE
REUSE_GATE_RECOMMENDATION != CORRECT_ARCHITECTURE
CONTEXT_PACKET != COMPLETE_REPOSITORY_STATE
LEXICAL_SCORE != EMBEDDING_OR_SEMANTIC_PROOF
PASSIVE_INDEX_REFRESH != AUTONOMOUS_PERMISSION_TO_WRITE
```

R0.1→R0.2 is intentionally a deterministic retrieval/architecture baseline. A future semantic ranker may improve recall, but it must preserve provenance classes and OAK separation rather than converting similarity into truth.

## Next bounded generations

- **R0.3 Temporal supersession miner** — candidate lineage from diffs/history, always review-gated unless explicit.
- **R0.4 Residual Code Compiler** — create only missing interfaces after exact-candidate inspection.
- **R0.5 Reuse Outcome Learning** — learn which reuse/compose/extend choices reduce defects, complexity, latency and maintenance using M+/M− receipts.
- **R0.6 Cross-repository Capability Graph** — combine PR memory with Master Doc Atlas source receipts and exact symbol provenance.
- **R0.7 LLMT federation** — Global GitHub LLMT supplies compact contexts to PR/Module LLMT identities sharing one canonical memory substrate.
