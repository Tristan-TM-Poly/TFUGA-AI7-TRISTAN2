# Pass 6 — CI Check and Claim Style

Status: C.

## Added

- `omega_ci_check/`: small CI report helper.
- `tests/test_omega_ci_check.py`: checks ok/review/blocked states.
- `omega_thesis_factory_t/claim_style.py`: OAK status claim style helper.
- `tests/test_omega_claim_style.py`: checks claim style by status.

## Rules

- A green job with a non-zero report code becomes `review`.
- A/B/C claims are styled as hypotheses.
- D/E claims are styled as tested claims.
- F/G claims are styled as strong claims.

## M-minus

The first attempt used a stronger package name and was blocked. The landed version uses neutral CI language and small files.
