# ApprovalSentinel Audit V8.3

## Status

- Register: R3 governance prototype.
- Promotion path: R4 after CI evidence and reproducible review; R5 only after stable policy enforcement across multiple PRs.

## Thesis

The AI-BIGBOOK / AI-7 stack becomes more powerful when its external actions are constrained by explicit local approval.

```text
maximum_generation + minimum_unapproved_mutation = safe_fertility
```

## Thermodynamic lock

The ApprovalSentinel is a semi-permeable boundary around the system.

Allowed through the boundary:

- local patches,
- draft PRs,
- evidence reports,
- Red Team reports,
- generated specs,
- reproducible scripts,
- read-only CI checks.

Blocked at the boundary:

- direct push to main,
- secret extraction,
- repository secret injection,
- Render/Vercel deployment hooks,
- payments,
- credential access,
- self-replication,
- unapproved external mutation.

## Matrix of avoided entropy

| Sovereignty vector | Risk deposit | ApprovalSentinel action | Final state |
|---|---|---|---|
| CI/CD boundary | generated code with access to API keys or deploy hooks | pull_request + workflow_dispatch, contents: read | isolated read-only validation |
| Truth test | hallucinated integrations or unbounded claims | EvidenceGate, local script checks, R0-R5 status | claims cannot outrun evidence |
| Repository stasis | direct push corrupting main | draft PR, reviewable branch, no main mutation | merge remains an explicit human decision |
| Agent pantheon | symbolic agents escalating into unsafe actions | contracts + blocked actions + ApprovalSentinel | agents propose, gate decides |

## Pantheon order

```text
FORGE-PRIME may propose.
EVIDENCE-OAK may judge.
RED-SHADOW may attack.
OUROBOROS-OMEGA may guard.
ApprovalSentinel decides what crosses the local boundary.
```

## Canon equation

Let `G` be generative capacity, `V` verification, `R` Red Team resistance, `E` EvidenceGate, and `A` ApprovalSentinel.

```text
SafeOutput = A(E(R(V(G(input)))))
```

External action is allowed only if:

```text
approval == true
and evidence_level >= required_level
and blocked_actions == empty
and secrets_required == false
```

## Security canon

Zero-Action is not blind automation. It is the reduction of user burden while preserving user authority.

```text
The dragon may forge.
The vault remains closed.
The merge is a conscious act.
```
