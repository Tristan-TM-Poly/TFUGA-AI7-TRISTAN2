# Ω-RE-T∞ R0.3 — GitHub Validation Receipt

## Receipt scope

This receipt records software and materialization evidence for the R0.3 branch. It does not promote synthetic fixtures to empirical observations, completed external experiments or scientific discoveries.

## Source and transport verification

The fail-closed materializer verified:

- 16 independently hashed payload fragments;
- archive SHA-256 `b1eb6be9785649c6dc9b7fb1d8c85218ecf55b9fb296cc4404bd2940e3d9ad62`;
- an exact allowlist of 17 extracted files;
- the SHA-256 digest of every extracted file;
- rejection of absolute paths, parent traversal and unexpected members;
- refusal to overwrite divergent files;
- an additive `pyproject.toml` patch limited to two R0.3 CLI entries.

Obsolete transfer fragments that were not part of the verified fragment map were removed after successful materialization.

## GitHub Actions evidence

Materialization workflow:

```text
workflow: Omega RE R0.3 Materialize
run_id: 30768567906
job_id: 91551570429
result: success
```

The successful job completed all gates:

1. checkout and Python setup;
2. payload verification and extraction;
3. Python compilation;
4. complete Ω-RE R0.1–R0.3 test suite;
5. R0.3 CLI demonstrations;
6. deterministic RE-1024 generation;
7. JSON Schema, cardinality and digest checks;
8. post-test payload re-verification;
9. explicit-path commit and push.

Test receipt:

```text
71 tests passed
Python 3.11 materialization runner
all seven R0.3 CLI demonstration groups passed
```

Materialization commit:

```text
commit: 18e6223e86dd8fe420c4fd4835e0ea1357b16948
message: feat(omega-re-r03): materialize active causal RE-1024 forge
```

## RE-1024 snapshot

The materialized snapshot contains:

```text
64 synthetic parent fixtures
16 deterministic perturbations per fixture
1,024 materialized cases
194,750 JSON lines
frontier digest: b1e029f7d80e55f4d0e746b2c2e3a9cd3528b94e8352035e3df76b6d5df60e85
```

Its epistemic counters remain:

```text
logical_cases = 1024
materialized_cases = 1024
executed_cases = 0
software_tested_cases = 0
scientifically_verified_cases = 0
logical_space_is_not_execution = true
materialization_is_not_validation = true
```

The snapshot is therefore a deterministic software research atlas, not evidence that 1,024 experiments were performed.

## OAK status

```text
SOURCE_PAYLOAD_VERIFIED
SOFTWARE_TESTED_ON_MATERIALIZATION_RUNNER
RE1024_DETERMINISTICALLY_MATERIALIZED
EXTERNAL_EXECUTION_NOT_CLAIMED
SCIENTIFIC_VALIDATION_NOT_CLAIMED
MERGE_NOT_AUTHORIZED_BY_THIS_RECEIPT
```

## Remaining integration gates

Before an eventual merge, the branch must still:

- pass the repository's ordinary pull-request validation workflows on a human-authored head;
- reconcile any new commits added to `main`;
- re-run the focused Ω-RE test matrix after reconciliation;
- preserve the additive `pyproject.toml` diff;
- remain subject to explicit human merge authorization.
