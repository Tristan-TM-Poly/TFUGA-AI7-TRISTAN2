# Outputs Policy

Issue: #57

This policy separates repository material from generated run material.

## Repository material

- Code.
- Tests.
- Documentation.
- Schemas.
- Small generated fixtures.
- Redacted examples.

## Generated material

Generated material should stay local by default.

Examples:

- Run outputs.
- Draft lists.
- Review queues.
- Large reports.
- Exports from source systems.

## Folder rule

The `outputs/` folder is for local run products. Commit only tiny fixtures, examples, schemas, or reviewed samples.

## Manifest rule

Shared outputs should record:

- source name;
- input summary;
- run date;
- record limit;
- tool version;
- checksum;
- review state.

## Review states

- `public_ok`
- `local_only`
- `review_required`
- `blocked`
