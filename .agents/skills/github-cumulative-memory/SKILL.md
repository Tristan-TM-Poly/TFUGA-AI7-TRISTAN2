# GitHub Cumulative Memory / Reuse-Before-Create

Use this skill whenever an agent or LLMT is about to design, extend, or implement a pull request in this repository.

## Governing invariant

```text
SEARCH → INSPECT → REUSE → COMPOSE → EXTEND → RESIDUAL ONLY → OAK
```

Never treat a new request as permission to create a new module from zero.

## Required workflow

1. Convert the requested work into a `CapabilityRequest` with:
   - description;
   - domains;
   - consumed tokens/interfaces;
   - produced tokens/interfaces.
2. Refresh or load `GitHubMemoryIndex`.
3. Run `ReuseBeforeCreateGate`.
4. Inspect the exact source/diff of the highest-ranked formal and historical candidates.
5. Follow the gate:
   - `REUSE`: use the existing capability and add only integration/tests needed;
   - `COMPOSE`: connect the selected capabilities before creating another implementation;
   - `EXTEND`: modify/adapt the strongest existing component and implement only `residual_outputs`;
   - `INSPECT`: do not create yet; exact inspection is mandatory because similarity is not semantic equivalence;
   - `CREATE`: new implementation is allowed only after the retrieval result has no meaningful existing candidate.
6. Run tests/OAK on the candidate commit.
7. Record explicit PR lineage in the PR body when known:

```text
reuses: #<PR>, #<PR>
extends: #<PR>
derived_from: #<PR>
supersedes: #<PR>
```

8. Keep M+, M−, M?, and superseded history distinct. `merged` alone is never M+.

## Context discipline

Do not load the repository wholesale into the model context. Use progressive zoom:

```text
PR summaries
→ capability/asset candidates
→ changed filenames
→ public symbols/interfaces
→ exact source/diff only for top candidates
```

The global memory may be large; the PR LLMT should receive the smallest context packet that preserves the relevant evidence and lineage.

## Existing foundations to prefer

- Ω-CAPABILITY-OS-T∞ `Capability` and Capability Genome;
- Ω-MASTER-DOC-ATLAS-T∞ structural/provenance inputs;
- existing HGFM/ChatMem memory surfaces when available;
- existing OAK and M+/M− evidence paths;
- existing Cognitive ISA / sparse coalition principles rather than duplicating an agent router.

## Hard OAK boundaries

```text
PR similarity != semantic equivalence
changed filename != reusable behavior
merged PR != successful capability
same component name != same implementation
candidate reuse != validated integration
large reuse percentage != better architecture by itself
```

If exact inspection disproves a candidate, preserve that result as negative retrieval evidence instead of repeatedly rediscovering the same false match.
