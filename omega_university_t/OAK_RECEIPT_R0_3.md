# Ω University R0.3 — OAK Receipt

## Scope

R0.3 adds a bounded software court for frozen assessment manifests, observed pre/post learning deltas, structural OOD probes, and prerequisite ablation fixtures.

It does **not** establish that a learner truly acquired a capability, that an intervention caused an improvement, that a benchmark was independently held out in the real world, or that a prerequisite should be removed from a production curriculum.

## Executable objects

- `FrozenAssessment`
- `LearningObservation`
- `LearningGainResult`
- `OODProbeResult`
- `PrerequisiteAblationCase`
- `PrerequisiteAblationResult`

## Hard OAK boundaries

```text
ObservedGain != CausalProof
CausalReviewEligible != CausalProof
FrozenAssessment != IndependentAssessment
HoldoutMetadata != ProvenSecrecy
OODContext != TransferProof
CandidateRedundantUnderFixture != GloballyRedundant
AblationResult != PermissionToRemovePrerequisite
Assessment != Credential
SoftwarePASS != EducationalEffectiveness
LocalPASS != GlobalPASS
```

## Fail-closed behavior

R0.3 rejects or de-qualifies:

- observations whose assessment digest does not exactly match the supplied frozen manifest;
- scores outside `[0,1]`;
- duplicate item identifiers inside a frozen assessment;
- causal-review eligibility when any required structural flag is missing;
- generator-exposed or non-holdout assessments from the causal-review gate;
- prerequisite ablations using incomparable sampling or different assessment manifests;
- negative ablation tolerances.

## What `causal_review_eligible` means

It means only that the caller supplied all of these metadata conditions:

1. randomized assignment;
2. concurrent control;
3. independent evaluator;
4. holdout assessment;
5. assessment marked as not exposed to the generator.

R0.3 does not authenticate those claims and never sets `causal_claim_proven=True`.

## What `CANDIDATE_REDUNDANT_UNDER_FIXTURE` means

It means only that the bounded ablated fixture did not fall below the retained-prerequisite fixture by more than the declared tolerance under structurally comparable metadata.

It does not establish global prerequisite redundancy and never authorizes a graph mutation.

## M− seeds

- benchmark leakage hidden behind caller metadata;
- repeated-test/practice effects mistaken for learning;
- cohort selection bias mistaken for intervention gain;
- same-source evaluation mislabeled independent;
- short-term gain mistaken for retention;
- OOD label chosen cosmetically while task structure remains in-distribution;
- one-target prerequisite ablation generalized to all target capabilities;
- small fixture equivalence promoted into institutional policy.

## Promotion frontier

Before any stronger educational-effectiveness claim, require external protocols with real participants or appropriately independent operational tasks, preregistration where relevant, uncertainty/statistical treatment, retention windows, independent assessment custody, negative controls, replication, privacy/consent review, and domain-appropriate ethics/governance.
