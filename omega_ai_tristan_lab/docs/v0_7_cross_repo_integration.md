# Ω-TRISTAN-RUNTIME v0.7 — Pinned Cross-Repository Integration

v0.7 moves from a generic capability fabric to a **bounded real integration profile** across three repositories.

```text
PEFA-FractalEnergySystem
  pefa-omega-em2.cvcd-extract
        ↓
TTM-TFUGA-AI7-TRISTAN2
  tristan-omni-core.evidence-to-idea
        ↓
TFUGA-AI7-TRISTAN2 / Ω-AI-TRISTAN-LAB
  tristan.idea.analyze
        ↓
TIR + ExecutionCapsules + OAK analysis
```

## Exact peer pins

The runtime does not use `main`, `master`, or another floating Git ref for the integration profile.

| Peer | Adapter provenance | Exact commit | Visibility |
|---|---|---|---|
| PEFA | `feat/tristan-runtime-adapter-r01` | `32b82d5d9818bfdd514eabf9e6ffefc520cc9260` | private |
| Omni-Core | `feat/tristan-runtime-adapter-r01` | `29e77ad2e1214eb536043b31670071f5079285a5` | public |

The branch names are provenance only. Installation targets emitted by `IntegrationLock` use the immutable commits.

## CLI

```bash
omega-tristan-runtime integration-lock
```

By default this command emits only public install targets. A private PEFA target is shown only when explicitly requested:

```bash
omega-tristan-runtime integration-lock --include-private-targets
```

This does not authenticate, clone, or install anything; it only renders the validated contract.

## Adapter maturity

`RepoRegistry` adds an `adapter-candidate` state. It is deliberately below `package` maturity. A candidate adapter must still pass exact-head CI and human review before promotion to a default branch.

The first PEFA CI attempt produced a useful M-minus result: editable package installation succeeded, but importing `pefa_omega_em2` revealed an undeclared NumPy runtime dependency through the historical eager package initializer. The packaging metadata was corrected to declare `numpy>=1.26`; the test was not weakened.

## OAK boundary

This profile is intended to prove software composition, not scientific correctness.

A green pipeline would establish only that:

1. three Python distributions can be installed together;
2. their entry points are discoverable through `tristan.plugins`;
3. the named capabilities execute in the declared order;
4. structured output crosses repository boundaries;
5. TIR/provenance/capsules are emitted by the host runtime;
6. the final OAK analysis exists.

It would **not** establish:

- independent reproduction of PEFA models;
- physical validity of a CVCD invariant;
- truth of an OAK-generated claim;
- product-market fit or monetary value;
- patentability;
- permission to merge or publish the peer branches.

## Promotion gate

The profile remains `CANDIDATE_PENDING_EXACT_HEAD_CI` until the exact pinned PEFA/Omni adapter heads and the real cross-repository workflow pass. Promotion must update the lock rather than silently following a moving branch.
