# Ω-WORKMAX-GIT-T∞ R1 — Cross-Repository WorkGraph

Status: **read-only cross-repository routing prototype / immutable snapshots / OAK review required**

## Mission

R1 routes one intent across multiple repositories without copying every repository into one monolith. Repository identity is `owner/repository@40-character-head-sha`. A capability is valid only when its bound SHA equals the declared repository snapshot SHA; stale bindings fail closed.

## Repository snapshot

Each snapshot carries repository full name, exact head SHA, default branch, exact source ref, visibility and declared technical authority. Supported authority metadata is `DISCOVER`, `READ`, `READ_PLAN`, `DRAFT_WRITE`; even `DRAFT_WRITE` does not authorize a write.

## Capability hypergraph

Cross-repository capabilities retain stable IDs, repository/SHA binding, domains, evidence weight, maturity, read-only state, dependencies and limitations. Dependencies can cross repository boundaries. Closure is deterministic and cycles fail closed.

## Privacy

Private repositories route through opaque capability metadata only. R1 does not embed private source content in the plan.

`private repo → opaque capability metadata → routing decision ≠ source disclosure`

## Multi-repository routing

The router transparently compares intent tokens with capability IDs, names, domains and limitations, with a bounded evidence bonus. The ranked set, its dependency closure and all exact repository identities are retained. This is discovery evidence, not semantic proof.

## First six-repository snapshot

The fixture binds the six owner repositories visible through the connected GitHub installation:

- `PEFA-FractalEnergySystem main@f06f47b…`
- `TFACC main@ce6ca0a…`
- `TFUGA-AI7-TRISTAN2 feat/omega-workmax-git-r01@8ead7d6…`
- `Tristan_Tardif-Morency_TFUG main@0877c90…`
- `Tristan_Tardif-Morency_TFUGAG main@96c9258…`
- `TTM-TFUGA-AI7-TRISTAN2 main@017e546…`

The broad fixture intent returns six relevant capabilities and six planned repository identities. Private PEFA/TFACC matches retain `opaque_private_capability_metadata_only`.

## CLI

```bash
python -m omega_workmax_t.cross_repo examples/omega_workmax_cross_repo_r1.json --output /tmp/workmax-cross-repo.json
```

No `pyproject.toml` entry is required.

## OAK boundaries

R1 does not claim semantic equivalence from lexical routing, current validity after a head changes, permission to disclose private content, permission to mutate repositories, legal/IP/safety authority from dependency closure, or global optimality across all branches.

## Next

R1.1 should ingest exported Ω-CHATGIT Universal Capability Contracts. R1.2 should compile cross-repository PR/issue delta packs. R1.3 should add cross-repository critical-path and validation-absorption scheduling while preserving independent repository authority and rollback boundaries.
