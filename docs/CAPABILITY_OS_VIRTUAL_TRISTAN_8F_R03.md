# Capability OS Virtual Tristan — Eighth Fire R0.3

R0.3 places a beneficiary-flow court above the existing Virtual Tristan runtime and minimum-swarm court. It does not create a new agent ontology.

## Objective

A Virtual Tristan is successful only when a declared beneficiary receives durable capability without unacceptable dependency, capture, missing consent, or irreversible harm.

The diagnostic quantity is:

`capability_left_behind + autonomy_gain + forkability_gain + reciprocity - dependency_created - capture_risk - irreversible_harm`

This score is never compensatory. Hard gates decide.

## Non-compensatory gates

A beneficiary flow is HOLD when any declared threshold fails, including missing consent, missing attribution, insufficient capability left behind, insufficient autonomy or reciprocity, excessive dependency, excessive capture risk, irreversible harm, or excessive dependency half-life.

## Beneficiary n+1

The swarm court receives an explicit expected-beneficiary set. Any expected beneficiary absent from the supplied flows causes `beneficiary_n_plus_one_failure`.

This is only a finite declared-list check. It does not prove that all morally relevant beneficiaries have been discovered.

## Apoptosis

A Virtual Tristan can be marked `apoptosis_ready` only after the beneficiary flow passes and both declared dependency creation and dependency half-life reach zero. This means the current declared intervention no longer requires persistent dependency; it does not prove the capability is universally self-sustaining.

## OAK boundaries

- CapabilityLeftBehind != VerifiedLongTermEmpowerment.
- DiagnosticScore != MoralScore.
- ConsentPresent != PerfectConsent.
- ExpectedBeneficiarySet != CompleteBeneficiarySet.
- LowDependency != NoHiddenDependency.
- ApoptosisReady != PermissionToDeleteEvidenceOrObligations.
- PASS != MoralCorrectness or causal proof.

## 8e Feu law

The runtime optimizes for capability left behind and autonomy while treating dependency, capture, consent, attribution, and irreversible harm as non-compensatory governance constraints.
