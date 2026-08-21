# Ω-META-THEORY-EVOLUTION R0.8 — Causal Challenge Credit & Frozen Evaluation

R0.8 executes the n+1 falsifier left by R0.7: an independent challenge court is insufficient if challenge evolution itself can redefine the success criterion or if challenge mutations are chosen without evidence that they discriminate candidate repairs.

## Core law

```text
ChallengeGeneration != ChallengeEvaluation
ChallengeAttribution != CausalProof
MetricMutation != AllowedDuringEvaluation
Tie != Winner
```

## Frozen evaluator

`FrozenEvaluator` binds an evaluator identity, criterion identity and transfer threshold before challenge selection. The system-under-test cannot change these fields during the evaluation call.

Role separation is enforced operationally:

```text
Generator != Verifier != ChallengeAuthority
ExternalEvaluator not in {Generator, Verifier}
```

Identity separation is a governance invariant only; it does not establish statistical or organizational independence in the external world.

## Challenge credit

`challenge_credit(...)` compares before/after bases under the same rule set and declared challenge families. It records:

- before retained ratio;
- after retained ratio;
- ratio gain;
- observables newly resolved;
- observables still missing.

This is counterfactual attribution under a supplied intervention pair, not proof that the challenge caused the repair.

## Information-guided challenge mutation

`mutate_challenge_by_information_gain(...)` creates only one-observable mutations of a declared seed challenge. Each mutation is evaluated over a finite candidate-basis population using frozen criteria.

The discrimination proxy is:

```text
IG_proxy = 4 p (1-p)
```

where `p` is the fraction of candidate bases that pass. The proxy is maximal when the mutation splits candidates evenly and zero when every candidate gets the same verdict.

Selection rules:

- unique positive maximum -> `PASS` and select;
- equal maxima -> `HOLD`;
- zero discrimination -> `HOLD`;
- collapsed authority -> `HOLD`;
- missing candidate population -> `HOLD`.

No scalar tie-break is introduced.

## OAK boundaries

- The information-gain score is an operational finite discrimination proxy, not Shannon information unless a probability model is explicitly supplied.
- Challenge credit is attribution, not causal proof.
- Frozen finite evaluation is not universal robustness.
- A unique discriminating mutation is not necessarily the globally best experiment.
- Semantic novelty, real-world relevance and source independence remain separate obligations.
- The evaluated system has no authority to redefine the frozen criterion inside this court.

## Cross-domain generalization

The pattern can be reused for:

```text
code patches       -> mutation tests selected by differential failure
scientific models  -> experiments selected by competing-model discrimination
automations        -> replay scenarios selected by policy disagreement
documents          -> reader/task probes selected by outcome discrimination
agents              -> external task suites selected by behavioral disagreement
```

The invariant is not the domain-specific score. It is the governance structure:

```text
candidate population
-> frozen evaluator
-> discriminating challenge population
-> explicit tie/HOLD
-> external re-evaluation
```

## n+1 residual

If R0.8 survives, the next falsifier should attack the finite candidate population and proxy itself:

- challenge selection under distribution shift;
- calibration of discrimination proxy against actual downstream error reduction;
- causal ablation of challenge families;
- source-independence graph for evaluator/challenge provenance;
- adaptive stopping when additional challenges add negligible verified information.

R0.8 does not claim these are solved.
