# Ω-COMPANY-AUTOPILOT-T R0.1

A bounded Company OS for a founder-controlled parent operating company and its internal divisions.

## Epistemic and legal boundary

This software does not create, register, incorporate, license, certify, sign for, file for, bank for, or legally recognize a company. It prepares records, schedules, decisions, evidence packets, dry runs, and explicitly authorized actions. Legal, fiduciary, tax, banking, securities, employment, IP-transfer, and government acts remain human-controlled and may require qualified professional review.

## Core loop

```text
OBSERVE -> PLAN -> OAK GATE -> APPROVAL -> EXECUTE -> EVIDENCE -> M- -> REGENERATE
```

## Recommended initial topology

```text
Tristan Parent OpCo (candidate legal entity)
├── Tristan OAK Systems
├── Tristan Software Labs
└── Tristan Research Foundry
```

Other concepts remain divisions or fertile backlog until spinout evidence exists.

## Autonomy target

- L5 supervised operations for low-risk reversible internal workflows.
- L3 approval for financial or external actions.
- professional review plus human execution for legal, tax, banking, securities, contracts, IP assignments, and hiring commitments.
- L0/L1 for exceptional critical acts.

## Safety invariants

1. No official identifier is invented.
2. No legal state transition occurs without explicit operator-supplied evidence.
3. No external execution occurs by default.
4. Approval records are bound to the current action hash.
5. A changed action invalidates old approvals.
6. Separate approvers are required when the gate requires two approvals.
7. Professional-review actions cannot be executed through the generic executor.
8. Payment preparation never implies payment execution.
9. Provider acceptance is not proof of legal completion.
10. GitHub stores schemas, synthetic examples, and redacted evidence references—not secrets or identity documents.

## Modules

| Module | Role |
|---|---|
| `models.py` | typed company, division, action, obligation, approval and receipt records |
| `registry.py` | constrained state machine and evidence-aware identity registry |
| `policy.py` | OAK autonomy gate |
| `deadlines.py` | T-90 to due-date planning |
| `treasury.py` | reserves and payment proposals, no bank execution |
| `spinout.py` | division-to-subsidiary evidence scoring |
| `approvals.py` | SHA-256-bound approvals |
| `execution.py` | dry-run first, explicit external-action interlocks |
| `evidence.py` | append-only hash-chained evidence ledger |
| `governance.py` | founder/board review pack |
| `autopilot.py` | observe-plan-gate-execute orchestration |
| `policy_atlas.py` | CVCD mass-policy atlas decoder and auditor |

## CLI

```bash
omega-company-autopilot init private/company.json
omega-company-autopilot status private/company.json
omega-company-autopilot add-division private/company.json tristan_materials "Tristan Materials" --mission "Materials R&D"
omega-company-autopilot board-pack private/company.json --out private/board-pack.json
omega-company-autopilot allocate-receipt 10000
omega-company-autopilot propose-payment private/company.json --action-id PAY-001 --division tristan_oak_systems --amount 250 --counterparty Vendor --category software --invoice-id INV-001 --known-vendor --out private/payment.json
omega-company-autopilot gate private/company.json private/payment.json
omega-company-autopilot approve private/payment.json --approval-id APR-001 --approver Tristan --reason "Invoice and vendor verified" --out private/approval.json
```

## External execution interlock

The generic executor requires both:

```text
OMEGA_COMPANY_EXTERNAL_EXECUTION=I_ACKNOWLEDGE_ONE_ACTION
OMEGA_COMPANY_ALLOWED_ACTION_ID=<exact action id>
```

A real adapter must also be supplied. The repository intentionally contains no bank, government, signature, payroll, or contract-acceptance adapter.

## Company state machine

```text
IDEA
-> CANDIDATE_LEGAL_ENTITY
-> PROFESSIONAL_REVIEW
-> FILING_READY
-> FILING_SUBMITTED
-> REGISTERED or INCORPORATED
-> POST_FORMATION
-> OPERATING
-> PRODUCTION_AUTHORIZED
```

`M_MINUS_HOLD` can interrupt the process when evidence, compliance, security, finances, or identity conflict.

## Policy atlas

The materialized atlas covers:

```text
16 divisions × 24 processes × 8 risk modes × 6 autonomy levels × 3 layers
= 55,296 policy cells
```

The three layers are `plan`, `gate`, and `evidence`. The cells are synthetic governance specifications, not legal determinations or completed corporate acts.
