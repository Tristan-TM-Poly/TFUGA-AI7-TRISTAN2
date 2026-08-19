# Ω-MASTER-DOC-ATLAS-T∞ R1.0

## Purpose

Ω-MASTER-DOC-ATLAS-T∞ composes repository-level Ω-DOC-FACTORY R1.0 receipts into one cross-repository provenance atlas.

```text
repository mains
→ per-repository Ω-DOC artifacts
→ compact immutable source snapshots
→ module/content fingerprints
→ repository overlap matrix
→ shared component candidates
→ duplicate claim candidates
→ cross-repository evidence graph
→ OAK boundaries
→ deterministic master atlas
```

The atlas is deliberately conservative. Equal hashes establish identical bytes for the observed module content. Similar names establish only candidate structural correspondence. Review-only claim/evidence bindings are counted as documentation links and never promoted into evidence strength.

## R1.0 source campaign

The first campaign absorbs six owner repositories, including both public and private repositories, using the artifact IDs and SHA-256 digests retained in each source snapshot. The current frozen observation contains 5,206 Python module observations, 26,262 public-symbol observations and 33 explicit claim candidates.

Only five module-content hashes occur in more than one repository. This is strong evidence against treating the six repositories as simple mirrors; the atlas therefore models them as related repository roots rather than forcing a canonical merge.

## OAK boundaries

- `REPOSITORY_PRESENT != FUNCTIONAL_SYSTEM`
- `MODULE_HASH_EQUALITY != SEMANTIC_EQUIVALENCE`
- `COMPONENT_NAME_MATCH != SHARED_IMPLEMENTATION`
- `REPOSITORY_OVERLAP != SUPERSESSION`
- `CLAIM_DUPLICATE != CLAIM_TRUE`
- `REVIEW_BINDING_VOLUME != EVIDENCE_STRENGTH`
- `ARTIFACT_ARCHIVED != INDEPENDENT_REPLICATION`
- `GRAPH_CONNECTIVITY != CAUSALITY_OR_PROOF`
- `DOCUMENTATION_COVERAGE != CLAIM_VALIDITY`

## Next evidence growth

R1.1 should ingest explicit execution receipts from each repository and replace synthetic repository-root wrapping with repository-native system discovery where possible. Cross-repository canonicalization should remain a separate OAK decision based on provenance, lineage and semantic equivalence rather than path/name similarity.
