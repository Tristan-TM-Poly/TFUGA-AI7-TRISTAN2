# PR #220 Stack Index

## Layer order

1. Ω-BIOTOX-PHARMA-GUARDIAN-T
2. AIT-BIO-OAK-GUARDIAN-T
3. AIT-SURVIVABLE-POWER-REVOLUTION-T
4. AIT-BIO-OAK-TOP64-PILLARS-T
5. Ω-AIT-IMMUNOME-T
6. Ω-DMT-WORLDMODEL-AIT-T
7. Ω-HALLUCINATION-LAB-REALITY-ANCHOR-T
8. Ω-AIT-REALITY-FORGE-T
9. Ω-AIT-CANON-OS-T
10. Ω-AIT-RESEARCH-FACTORY-T
11. Ω-AIT-NO-HUMAN-BOTTLENECK-T
12. Ω-AIT-CONTINUATION-ENGINE-T
13. Ω-AIT-AUTONOMOUS-PROPULSION-MESH-T
14. Ω-AIT-SELF-STABILIZING-REFACTOR-KERNEL-T

## Current draft status

This PR is intentionally draft-only. It creates a large OAK-safe architecture and should be split into focused follow-up PRs after review.

## Smoke-test progress

- Import smoke test exists: `tests/test_pr220_import_smoke.py`
- Focused matrix exists: `configs/pr220_focused_test_matrix.yaml`
- Progress report exists: `docs/oak_reports/pr220_import_smoke_progress.md`

## Safe next work

- Run focused pytest groups in a controlled CI or local sandbox.
- Split packages by layer after review.
- Normalize fallback filenames created due to connector filtering.
- Keep no-auto-merge policy.
