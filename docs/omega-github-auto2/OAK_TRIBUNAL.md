# Omega AUTO2 OAK Tribunal

The AUTO2 reactor must pass an OAK tribunal before a generated card can move from draft artifact to implementation.

## Judges

1. **Structure** — Top1024 invariant holds: 16 domains x 4 sectors x 16 atoms.
2. **Reproducibility** — outputs are deterministic from the config.
3. **Tests** — unit tests exist for core invariants.
4. **Safety** — irreversible actions remain blocked.
5. **IP / secret** — ECC and patent-review material remain non-public until reviewed.
6. **Revenue claim safety** — billing meters are simulated until approved.
7. **Regulated-domain warning** — pharma, compliance, and customer-sensitive material require review.
8. **M-minus logging** — failure modes become memory rather than deletion.

## Tribunal statuses

- `PASS`: safe and complete.
- `PASS_WITH_LOCKS`: safe only with human locks preserved.
- `FAIL`: missing invariant, unsafe claim, or unreviewed sensitive action.

## Required output

The factory writes:

```text
artifacts/omega_github_auto2/oak_tribunal_report.json
```

This report is the canonical pre-merge evidence for AUTO2 expansions.
