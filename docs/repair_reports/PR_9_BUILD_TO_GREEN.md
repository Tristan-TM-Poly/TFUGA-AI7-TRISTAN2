# PR #9 Build-To-Green repair report

PR: `#9 — FTPCI-Ω / AIT-Ω / JKD-YY3-Tristan² / Ω-MGHFM-TGNT engines`

## Decision

`manual_required`

## Why this PR is not merged automatically

The PR is non-draft, but it is not mergeable against `main`. The PR body already documents an add/add semantic conflict around:

```text
docs/omega-mghfm-tgnt-prime-tensors.md
```

Because this file is a canon/theory artifact, automatic conflict resolution would risk deleting or overwriting meaningful theory content. Under OAK, this must not be solved by force-push, blind overwrite, or auto-merge.

## Safe Build-To-Green plan

1. Inspect the `main` version and PR branch version of `docs/omega-mghfm-tgnt-prime-tensors.md`.
2. Preserve all non-duplicate canon content from both sides.
3. Prefer a structured merge that separates:
   - stable definitions;
   - executable prototype notes;
   - speculative fertile ideas;
   - OAK warnings and falsification tests;
   - M⁻ anti-overclaim memory.
4. Run the PR validation commands:

```bash
python -m unittest tests/test_tristan_engines.py
python -m unittest tests/test_omega_mghfm_tgnt.py
python scripts/run_all_tristan_engines.py
```

5. Re-check mergeability and CI.
6. Merge only if the PR becomes non-draft, clean, mergeable, and green with expected head SHA.

## Forbidden actions

- Do not force-push.
- Do not delete either side of the canon conflict blindly.
- Do not mark conflict resolved without preserving OAK warnings.
- Do not bypass branch protection.
- Do not merge while `mergeable=false`.

## OAK invariant

```text
Conflict resolution = semantic synthesis, not mechanical overwrite.
Canon preservation > speed of merge.
```
