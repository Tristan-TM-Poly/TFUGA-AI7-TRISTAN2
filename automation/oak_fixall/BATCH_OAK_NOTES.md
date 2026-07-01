# Batch OAK Notes

The batch layer is intentionally weaker than live GitHub verification.

It can answer:

- Which decisions appear most often?
- Which blockers repeat?
- Which repos contain the most blocked items?
- Which items need human approval or cooldown?

It cannot answer:

- Whether a PR is still mergeable now.
- Whether a head SHA changed after the decision file was created.
- Whether external statuses changed.
- Whether a human has approved a sensitive override.

Therefore, batch output is advisory only.
