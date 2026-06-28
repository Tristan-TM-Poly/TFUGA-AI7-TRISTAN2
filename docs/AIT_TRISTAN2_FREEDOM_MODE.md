# AIT-Tristan2 FREEDOM MODE

AIT-Tristan2 FREEDOM MODE is the execution-delegation layer above Ω-CORP-JARVIS-T and Ω-AUTO²-CORP-JKD.

## Mission

```text
Remove avoidable founder friction through automation, delegation, compressed decisions, and confirmation records.
```

## Principle

```text
The founder should control the system, not perform every task.
```

## Architecture

```text
AIT core -> action classifier -> automation queue -> delegate mesh -> confirmation record -> OAK memory
```

## Queues

| Queue | Purpose |
|---|---|
| AUTO_NOW | safe internal execution |
| APPROVE_ONE_TAP | compressed founder approval |
| DELEGATE | assigned to scoped delegate or service |
| REVIEW_GATE | requires qualified review before action |
| WAITING_FOR_PROOF | waiting for confirmation record |
| M_MINUS_HOLD | blocked by uncertainty or risk |

## Files

| File | Role |
|---|---|
| `company_os/ait_tristan2/freedom_protocol.yaml` | FREEDOM-100 protocol and queues |
| `company_os/ait_tristan2/delegate_mesh.yaml` | delegate roles, scopes, controls |
| `company_os/ait_tristan2/mandate_pack_template.md` | scoped delegation template |
| `company_os/ait_tristan2/execution_card_schema.yaml` | execution card schema |
| `company_os/ait_tristan2/decision_card_schema.yaml` | compressed decision schema |
| `company_os/ait_tristan2/confirmation_record_schema.yaml` | confirmation record schema |

## OAK rule

```text
External completion requires confirmation evidence.
Prepared packets are not completed actions.
```

## Friction KPIs

```yaml
friction_kpis:
  human_minutes_per_week: "<= 5"
  physical_actions_per_month: 0
  unprepared_external_actions: 0
  confirmation_records_percent: 100
  founder_decision_format: "A/B/C or yes/no"
```

## Canonical phrase

```text
AIT-Tristan2 does not replace authority; it builds the execution mesh around authority.
```
