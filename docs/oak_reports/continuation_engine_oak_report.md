# OAK Report — Ω-AIT-CONTINUATION-ENGINE-T

## Scope

ContinuationEngine ensures every state produces a safe next move. It converts missing inputs, uncertainty, review thresholds, and blocked tasks into safe artifacts.

It does not authorize high-impact external action, publishing, merging, deployment, irreversible change, or review-gated decisions.

## OAK status

- **Observe:** detect blocked tasks, missing inputs, uncertainty, risk, and current motion state.
- **Act safely:** create artifacts such as tests, reports, simulations, draft PRs, notes, and M− entries.
- **Kill-risk:** route to review packet, quarantine note, or safe-next-action-only when direct movement is not safe.

## Core boundaries

1. Every state must produce a safe next move.
2. BLOCKED is never final.
3. Missing input becomes assumption, safe default, or test.
4. Direct action is replaced by safe artifact when needed.
5. Cognitive work is conserved as artifact, M−, residue, test, or note.
6. Priority chooses useful safe action, not impressive unsafe action.
7. No auto-merge and no auto-publish.

## Review checklist

- SafeNextActionKernel should map missing proof/test/data/safety to safe artifacts.
- FallbackLadder should descend until a safe action exists.
- TaskGraph should convert BLOCKED to SAFE_ALTERNATIVE.
- MissingInputSynthesizer should mark uncertainty and safe defaults.
- DeadEndConverter should produce safe artifacts.
- PriorityEngine should penalize risk, cost, and uncertainty.
- SelfPropellingLoop should always return a packet.

## Final law

```math
\boxed{\text{Every state must produce a safe next move.}}
```
