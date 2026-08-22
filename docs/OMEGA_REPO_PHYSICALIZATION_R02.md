# Ω Repo Physicalization R0.2

This increment turns issue #462 from a repository-creation wish into an evidence-bound source extraction plan.

## First pair

### `omega-protocol` — target PUBLIC

Current-main source court:

- `capability.ir` → `omega_capability_os_t/core.py::Capability` — `CANON_MAIN`
- `workunit.schema` → `omega_intent_t/models.py::WorkUnit` — `CANON_MAIN`
- `repo.genome` → `omega_repo_genesis_t/plan.py::bootstrap_files` — `CANON_MAIN`
- `research.abi` — `HOLD_UPSTREAM` (#448)
- `transformation.receipt` — `HOLD_UPSTREAM` (#448)
- `evidence.receipt` — `HOLD_UPSTREAM` (#448)
- `artifact.ref` — `HOLD_UPSTREAM` (#448)

Result: `PARTIAL_READY`, not ready for repository creation.

### `tristan-observatory` — target PRIVATE

Current-main source court:

- snapshot publish/delta — `HOLD_UPSTREAM` (#452)
- history archaeology — `HOLD_UPSTREAM` (#450)
- temporal repo graph / code phylogeny — `HOLD_UPSTREAM` (#330)

Result: `HOLD_FOR_SOURCE_CONVERGENCE`.

## Physicalization law

Only source bindings marked `CANON_MAIN` with an explicit source path and source commit may enter an extraction payload.

Historical PR provenance is useful for reconstruction but is never treated as a current implementation.

```text
historical capability != canonical source
HOLD != failure
PARTIAL_READY != repository creation authority
```

## Public/private dependency law

A public target repository may not depend on a private target repository. Private repositories may consume the public protocol surface.

```text
omega-protocol [PUBLIC] -> tristan-observatory [PRIVATE]
```

never the reverse as a required build/import dependency.

## Authority boundary

This planner does not create repositories. Every emitted repository record has `repository_creation_authorized=false` until a separately authorized repository-creation surface is available and all required source bindings and public-visibility gates pass.
