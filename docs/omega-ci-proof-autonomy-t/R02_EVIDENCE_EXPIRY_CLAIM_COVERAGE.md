# Ω-CI-PROOF-AUTONOMY-T∞² R0.2

## Evidence Expiry, Claim Coverage and Constitutional Capabilities

R0.2 strengthens the A1–A3 kernel without granting repair, push, merge or release authority.

### Implemented

- evidence states: `CURRENT`, `STALE`, `EXPIRED`, `SUPERSEDED`, `INVALIDATED`, `REVOKED`;
- TTL from the shortest supporting claim;
- invalidation by affected package or required-test changes;
- staleness from dependency or environment drift;
- deterministic refresh requirements;
- claim coverage across positive, negative, oracle, falsifier, provenance, environment, limitation and required-kind dimensions;
- weighted portfolio coverage using explicit claim criticality;
- promotion proofs that only declare `ELIGIBLE_FOR_HUMAN_REVIEW`;
- semantic proof cache keys over claim, code slice, dependencies, environment class and test contract;
- machine-readable constitution capped at A3;
- scoped, temporary and revocable capability tokens;
- supply-chain audit requiring immutable 40-character action SHAs;
- reviewed pins for checkout 4.2.2, setup-python commit and upload-artifact release commit.

### OAK boundary

A current proof is not eternal truth. Claim coverage is a structured quality score, not a probability of correctness. A promotion proof does not itself mutate the claim registry or merge code. R0.2 performs no remote mutation at runtime and keeps `automatic_merge_allowed=false`.

### M-minus addressed

`M_MINUS-CI-SUPPLY-001`: R0.1 used moving major-version tags for GitHub Actions. R0.2 pins every external action used by its workflow to an immutable reviewed commit SHA and makes unpinned references a blocking audit error.
