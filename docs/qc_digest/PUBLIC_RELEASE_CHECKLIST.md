# Public Release Checklist

Issue: #57

Use this checklist before publishing code, docs, metadata scaffolds, or demos.

## Usually publishable

- Source code.
- Tests.
- Schemas.
- Generated sample data.
- Documentation.
- Local command examples.

## Review first

- Live outputs.
- Opportunity notes.
- Review queues.
- Generated reports from live sources.
- Notes that are not already public.

## Required checks

- [ ] Tests or validation path exists.
- [ ] Boundary is written.
- [ ] Known limits are written.
- [ ] Source manifest exists when data is used.
- [ ] Checksums exist when outputs are shared.
- [ ] Outputs folder rule is followed.
- [ ] Public/private boundary is clear.
- [ ] Evidence supports the claim.

## Outputs folder rule

Generated outputs stay local by default. Commit only small fixtures, examples, schemas, or redacted samples.

## Decision states

- `public_ok`
- `local_only`
- `review_required`
- `blocked`
