# Ω-AUTO²-CORP-JKD — Automation Rules

## Core doctrine

```text
Automate safe internal work.
Prepare external actions as review packets.
Queue actions that need approval.
Convert blockers into checklists.
Record risks as M-minus.
Only mark external actions complete after real confirmation.
```

## JKD principle

```text
Convert a blocker into a route: route -> checklist -> packet -> approval -> confirmed action.
```

## Routing

| Class | Action |
|---|---|
| FULL_AUTO | Execute internally and record outputs |
| HUMAN_APPROVAL | Prepare packet and queue for explicit approval |
| LEGAL_SIGNATURE | Prepare draft, add signature fields, require review |
| PROFESSIONAL_REVIEW | Generate memo and questions for professional review |
| FORBIDDEN_OR_UNSAFE | Redirect to safe alternative and record M-minus |

## Pseudocode

```python
def jkd_automate(task):
    classification = classify(task)

    if classification == "FULL_AUTO":
        return execute_internal(task)

    if classification == "HUMAN_APPROVAL":
        return queue_for_approval(prepare_packet(task))

    if classification == "LEGAL_SIGNATURE":
        return handoff(prepare_draft(task), minimal_human_steps(task))

    if classification == "PROFESSIONAL_REVIEW":
        return review_packet(generate_memo(task), generate_questions(task))

    return safe_redirect(task), record_mminus(task)
```

## Controlled external-status labels

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

## Safe transformations

| Blocked direct action | Safe transformation |
|---|---|
| external document execution | draft + review packet |
| official filing workflow | prefilled checklist + human submission gate |
| bank/account workflow | preparation packet + required documents |
| ROI claim | risk-adjusted ROAK scenario |
| registry identifier | pending until confirmed source record |
| outreach | draft + approval card |

## OAK product rule

```text
No product or corporate claim without residual, invariant, performance, risk, and confirmation evidence.
```
