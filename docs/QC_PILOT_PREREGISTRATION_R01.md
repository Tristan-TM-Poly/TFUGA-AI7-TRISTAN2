# Québec Pilot Preregistration R0.1

This artifact closes issue #521 at the protocol layer only. It does **not** create participants, observations, approvals, or evidence.

## Purpose

Freeze the smallest credible Québec pilot before outcomes are observed so later measurements can be compared against criteria that were not rewritten after seeing results.

Core invariants:

- `AcceptanceRate != SuccessGate`
- `SystemPerformedTask != BeneficiaryAcquiredCapability`
- `ProcessPASS != AdoptionPASS != PermissionToDeploy`
- `FROZEN != AUTHORIZED`
- `Generated != Verified`
- material system or consent change requires reconsultation
- personalized psychological targeting is denied
- null and negative results remain admissible outcomes

## Canonical flow

`Baseline -> Disclosure -> Choice -> Intervention if chosen -> Withdrawal -> IndependentTask -> DelayedReplay -> DependencyCheck -> SocialLegitimacyReceipt -> TransferEvidenceReceipt -> OAK/AuthorityDecision`

A participant or affected group may freely choose not to adopt. Zero adoption can coexist with a legitimate process.

## Machine-readable template

Start from:

`pilots/quebec/8f_capability_transfer_preregistration.template.json`

The checked-in template intentionally contains `TBD` placeholders. The preregistration court MUST return `HOLD` until every placeholder is replaced with real pre-outcome protocol information.

Do not replace placeholders with invented participants, invented institutions, synthetic outcomes, or simulated approval.

## What must be frozen before observation

The protocol freezes:

1. Québec jurisdiction and bounded context;
2. affected and intended beneficiary groups;
3. system and consent versions;
4. generator and evaluator identities/roles;
5. baseline, intervention, and at least one simpler/no-intervention alternative;
6. capability-transfer observable;
7. explicit system-withdrawal condition;
8. delayed replay window;
9. dependency measurement and ceiling;
10. understanding and agency thresholds;
11. opt-out, contestation, rollback, and evidence-disclosure mechanisms;
12. stakeholder representation and minority-residual preservation;
13. AcceptanceDebt ceiling;
14. material-change reconsultation rule;
15. decision set including `HOLD`, `REVISE`, `NO_ACTION`, and `PILOT_ELIGIBLE`.

## Three digests

A successful freeze produces:

- `protocol_digest`: hash of the complete preregistration;
- `legitimacy_criteria_digest`: hash consumed by the social-legitimacy court;
- `transfer_criteria_digest`: hash consumed by the prospective transfer court.

Any material protocol change changes at least the protocol digest. Changes to legitimacy or transfer thresholds also change the corresponding court digest.

## Authority separation

`authority_status` defaults to `UNRESOLVED`.

A protocol may be `FROZEN` while `execution_eligible == false`. This is deliberate: preregistration is an epistemic action, not permission to recruit, intervene, access data, or deploy.

Real execution requires the applicable institutional, legal, ethical, safety, privacy, and operational authority for the actual pilot context.

## HOLD conditions implemented in R0.1

The court HOLDs when:

- the jurisdiction is not Québec-first;
- any placeholder remains;
- outcomes were already observed;
- no alternative is defined;
- generator and evaluator collapse when separation is required;
- material-change reconsultation is disabled;
- personalized psychological targeting is enabled;
- acceptance rate is treated as a success gate;
- the decision criteria omit required negative/stop outcomes.

## OAK nonclaims

A `FROZEN` receipt does not establish:

- that the intervention works;
- that affected groups consent;
- that representation is complete;
- that the evaluator is statistically independent in practice;
- that the pilot is ethically or legally approved;
- that social legitimacy has been achieved;
- that capability transfer has occurred;
- that expansion outside Québec is justified.

The next evidence-bearing step is to fill the template with a real bounded Québec context **before** observing outcomes and then seek the applicable real-world authority. No R0.2 is justified merely by the existence of R0.1.
