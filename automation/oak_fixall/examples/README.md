# Ω-AUTO²-OAK-FIXALL-T Examples

These examples are local decision fixtures.

They do not represent live repository state and do not authorize any merge.

## Fixtures

- `clean_merge_candidate.decision.json`: a clean theoretical merge candidate.
- `draft_wait_candidate.decision.json`: a draft PR that must remain `WAIT_COOLDOWN`.
- `red_ci_blocker.decision.json`: a mergeable PR with red CI that must be `BLOCK_M_MINUS`.
- `hyperatlas_safe_extraction.decision.json`: a scope-mismatch / safe-extraction example.

## OAK rule

A fixture can test the logic, but live PR actions still require live GitHub verification.
