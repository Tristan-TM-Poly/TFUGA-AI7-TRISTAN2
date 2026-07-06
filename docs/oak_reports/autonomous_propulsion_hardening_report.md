# OAK Report — Autonomous Propulsion Mesh Hardening

## Scope

Stacked hardening above PR #220, based on `codex/omega-biotox-pharma-guardian-t-2026-07-06`.

This report records a safe follow-up branch for Ω-AIT-AUTONOMOUS-PROPULSION-MESH-T. It does not merge PR #220 and does not change deployment behavior.

## Changes

- Hardened `tools/propulsion_score.py` with positive mass, entropy mass, blocked candidate handling, review penalty, serializable audit explanation, ranking, and Infinite Useful Work fallback.
- Hardened `tools/task_queue_mesh.py` with Q0-Q10 validation, reversible safety selection, blocked-task conversion, priority tie-break, held/waiting/blocked introspection, and fallback next-action note.
- Added `tools/debt_burner.py` to convert visible debt into traceable queue tasks.
- Expanded tests for scoring, queue selection, fallback routing, blocked-task conversion, and debt conversion.

## OAK Boundaries

- Planning only.
- Draft PR only.
- No auto-merge.
- No deployment.
- No publication.
- No external contact.
- Risky or irreversible states route to review or safe alternatives.

## M-minus captured

- The PR #220 body describes ContinuationEngine and PropulsionMesh, but the first implementation remains mostly skeletal.
- `debt_burner.py` was listed in the intended Phase Beta payload but was not reliably fetchable on the PR head branch, so this branch adds it explicitly.
- A richer `oak_governor.py` hardening patch was intentionally not forced after write-guard rejection; this remains a follow-up task.

## Next safe action

Run CI for this stacked branch. If tests pass, keep it as a draft stacked PR against PR #220's head branch. If tests fail, convert the failure into a minimal reproducer, failing test, M-minus note, and small patch.
