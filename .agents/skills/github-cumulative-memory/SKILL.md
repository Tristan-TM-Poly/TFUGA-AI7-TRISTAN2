# GitHub Cumulative Memory / Reuse-Before-Create

Use this skill whenever an agent or LLMT is about to design, extend, or implement a pull request in this repository.

## Governing invariant

```text
SEARCH → INSPECT → REUSE → COMPOSE → EXTEND → RESIDUAL ONLY → OAK → LEARN → FEDERATE
```

Never treat a new request as permission to create a new module from zero.

## Required workflow

1. Convert requested work into a `CapabilityRequest` with description, domains, consumed interfaces and produced interfaces.
2. Refresh or load `GitHubMemoryIndex`.
3. Run `ReuseBeforeCreateGate`.
4. Progressively zoom only into the highest-ranked candidates: PR metadata → changed filenames → static symbols → exact source/diff.
5. Run `TemporalSupersessionMiner`; inferred temporal/file/lexical overlap is review-only and must never become a strong `supersedes` edge automatically.
6. Run `ResidualCodeCompiler` and obey its scope:
   - `REUSE` / `COMPOSE`: integration/tests only; no duplicate implementation;
   - `EXTEND`: implement only `residual_outputs`;
   - `INSPECT`: generation remains blocked pending exact candidate inspection;
   - `CREATE`: limit generation to the requested capability after retrieval exhaustion.
7. Run tests/OAK on the exact candidate commit.
8. Record explicit lineage in the PR body when known:

```text
reuses: #<PR>, #<PR>
extends: #<PR>
derived_from: #<PR>
supersedes: #<PR>
```

9. Record reuse outcomes only through evidence-bearing `ReuseOutcomeReceipt` objects. `merged` alone is never M+.
10. For cross-repository work, use `CrossRepositoryCapabilityGraph`; preserve same-ID contract conflicts instead of overwriting them.
11. For specialized PR/module LLMTs, use `LLMTFederationCompiler`. Context identities are logical projections over shared memory; authority is capped at `read`/`draft` and packet multiplicity is not independent evidence.

## Context discipline

Do not load the repository wholesale into model context. Use progressive zoom:

```text
all PR summaries
→ capability/asset candidates
→ top-k changed filenames
→ static symbols/interfaces
→ exact source/diff for top candidates
→ bounded LLMT packet
```

The global memory may be large; each PR/module LLMT should receive the smallest context packet that preserves relevant evidence, residuals, uncertainty and lineage.

## Existing foundations to prefer

- Ω-CAPABILITY-OS-T∞ `Capability` and Capability Genome;
- Ω-MASTER-DOC-ATLAS-T∞ structural/provenance inputs;
- HGFM/ChatMem memory surfaces where available;
- OAK and M+/M− evidence paths;
- Cognitive ISA / sparse coalition principles rather than duplicating an agent router;
- this cumulative-memory stack itself before creating another GitHub memory/retrieval layer.

## Hard OAK boundaries

```text
PR similarity != semantic equivalence
changed filename != reusable behavior
AST symbol exists != reusable behavior
inferred supersession != strong lineage
merged PR != successful capability
generation_allowed != GitHub write authority
reuse outcome != causal proof
same capability contract != shared implementation
multiple LLMT packets != independent evidence
candidate reuse != validated integration
```

If exact inspection disproves a candidate, preserve that result as negative retrieval evidence instead of repeatedly rediscovering the same false match.
