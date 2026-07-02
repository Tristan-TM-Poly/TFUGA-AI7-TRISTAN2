# PR Build To Green

`PR Build To Green` extends Green PR Merge from a passive merge watcher into a bounded construction and enrichment loop.

It does **not** mean force-merging broken work. It means moving a pull request toward a clean, reviewable, testable state before any merge is attempted.

```text
Open PR
  -> inspect metadata, files, checks, conflicts, OAK risks
  -> classify blockers
  -> enrich safely when possible
  -> rerun or wait for checks
  -> merge only when non-draft + clean + mergeable + expected SHA
  -> otherwise leave a repair report
```

## Decisions

| Decision | Meaning |
|---|---|
| `merge_now` | PR is non-draft, clean/green, mergeable, and can be squash-merged with expected SHA. |
| `auto_enrich` | PR is not green yet, but safe additive enrichment is possible. |
| `wait` | Checks are pending or queued; do not mutate or merge yet. |
| `manual_required` | Drafts, conflicts, semantic ambiguity, or safety risks require human judgment. |
| `skip` | No safe action is available. |

## Safe enrichment actions

Allowed actions are additive and reversible:

- add or repair tests;
- add documentation or OAK runbooks;
- add validators that prevent regressions;
- add safety guardrails for secrets, IP, public actions, permissions, money, health, and destructive effects;
- add repair reports for conflicts or manual blockers.

## Forbidden actions

The builder must not:

- mark a draft PR ready;
- force-push;
- delete branches;
- bypass branch protection;
- weaken or remove checks to make a PR green;
- auto-resolve semantic merge conflicts;
- expose secrets or credentials;
- perform public/legal/financial/health/destructive actions without explicit OAK approval.

## OAK invariant

```text
Green = reproducible cleanliness + passing checks + no unresolved risk.
Green != silenced failure.
Green != forced merge.
Green != weakened CI.
```

## Integration with Ω-ACTION-EXT-T

This module is a planning kernel. Real GitHub mutation should remain behind:

1. `ActionManifest` hash;
2. `OAKGate` decision;
3. dry-run connector plan;
4. approval queue when risk is non-trivial;
5. proof ledger;
6. merge with expected head SHA only after clean state.
