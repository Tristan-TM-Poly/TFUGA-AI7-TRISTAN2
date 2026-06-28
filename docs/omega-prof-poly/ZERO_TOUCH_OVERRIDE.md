# Ω-PROF-POLY-T — Zero-Touch Override

Status: canonical override for v0.1.

This file overrides any older wording in this module that suggests manual review as a normal workflow step.

## Rule

```text
ZERO-TOUCH BY DEFAULT.
```

Ω-PROF-POLY-T should automate routine checks through OAK gates, test packets, evidence ledgers, schema validation, risk scores, and reproducibility checks.

## Operational model

```text
input
-> generate artifact
-> run automated OAK checks
-> generate evidence/risk/status packet
-> continue if safe inside the repository/workspace
-> produce blocked-action packet when external permissions are missing
```

## Allowed automated outputs

- course maps;
- exercise banks;
- rubrics and policy drafts;
- lab protocol drafts;
- uncertainty checklists;
- reproducibility tests;
- grant packet drafts;
- IP classification drafts;
- project forge outputs;
- GitHub files, examples, schemas, tests, reports, and issues;
- OAK warnings and blocked-action packets.

## External-action lock

The system may generate all preparatory artifacts automatically. It should only lock actions that require external platform authority, legal authority, institutional authority, signatures, credentials, or account permissions unavailable to the runtime.

A lock is not a manual verification workflow. It is a capability boundary.

## M-minus correction

Any phrase such as `human review`, `professor review`, or `institutional review` in older module files should be interpreted as:

```text
automated OAK gate + evidence ledger + capability boundary for external actions
```

## Next implementation target

Replace older wording directly once the connector accepts the file update. Until then, this override is the canonical interpretation for Ω-PROF-POLY-T v0.1.
