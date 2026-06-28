# Ω-AUTO²-CORP-JKD

Ω-AUTO²-CORP-JKD is the automation doctrine for Ω-CORP-JARVIS-T official.

## Core idea

```text
What can be done safely is automated.
What cannot be completed directly is prepared as a packet.
What requires review is queued.
What creates risk is recorded as M-minus.
What is externally complete must have confirmation evidence.
```

## Modules added

| File | Role |
|---|---|
| `company_os/automation/action_classifier.yaml` | classifies actions by automation level |
| `company_os/automation/impossible_handler.yaml` | turns blockers into packets/checklists |
| `company_os/automation/live_auto_backlog.yaml` | action backlog for corporate, IP, sales, finance |
| `company_os/automation/jkd_automation_rules.md` | operating rules and statuses |
| `company_os/templates/review_packet.md` | compact review packet |
| `company_os/templates/founder_resolution_draft.md` | internal founder resolution draft |
| `company_os/templates/ip_review_packet.md` | internal asset/IP review packet |
| `company_os/templates/sales_offer_one_pagers.md` | initial commercial one-pagers |

## Automation classes

```text
FULL_AUTO
HUMAN_APPROVAL
LEGAL_SIGNATURE
PROFESSIONAL_REVIEW
FORBIDDEN_OR_UNSAFE
```

## Status labels

```text
pending_official_confirmation
pending_professional_review
pending_human_signature
pending_payment_or_submission
ready_for_internal_use
ready_for_review
m_minus_hold
confirmed_complete
```

## Rule

```text
Never represent a prepared packet as a completed external action.
```

## Canonical phrase

```text
Convert blockers into routes, routes into checklists, checklists into packets, and packets into approved actions.
```
