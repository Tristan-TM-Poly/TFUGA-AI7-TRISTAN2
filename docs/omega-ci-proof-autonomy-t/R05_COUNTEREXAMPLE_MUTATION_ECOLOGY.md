# Ω-CI-PROOF-AUTONOMY-T∞² — R0.5 Counterexample Forge and Mutation Ecology

R0.5 adds a bounded falsification layer below autonomy level A4.

## Pipeline

```text
claim contract
→ declarative mutants
→ finite mutation campaign
→ surviving mutants
→ counterexample search
→ minimization
→ metamorphic and differential checks
→ M⁻ rule and regression-test candidate
→ human review
```

## Implemented components

- `MutationCampaignEngine`: evaluates declared behavior mutants against a versioned finite test corpus.
- `CounterexampleForge`: searches a bounded deterministic seed space for witnesses that distinguish surviving mutants from the reference behavior.
- `MetamorphicEngine`: checks claim-level relations when a single expected output is insufficient.
- `DifferentialOracle`: compares reference and candidate behaviors across a shared corpus.
- `MMinusCompiler`: converts minimized counterexamples into structured M⁻ rules and Python regression-test candidates.
- `MutationEcologyEngine`: coordinates five specialized falsification agents and links all generated receipts.

## Fixture result

For exact relative-path normalization:

- 6 mutants declared;
- 3 killed by the existing finite tests;
- 1 survivor (`M-ALL-PREFIX`);
- 1 equivalent mutant explicitly separated;
- 1 invalid operator explicitly rejected;
- mutation score: `0.75`;
- weighted mutation score: `0.846154`.

The survivor is falsified by the minimized counterexample:

```text
input:    ././
expected: ./
observed: ""
```

This becomes a generated M⁻ candidate. It is not applied automatically.

## OAK boundary

All R0.5 outputs preserve:

```json
{
  "maximum_authority": "A3",
  "execution_authorized": false,
  "automatic_patch_allowed": false,
  "automatic_merge_allowed": false,
  "human_review_required": true,
  "remote_mutations": 0
}
```

R0.5 mutates only declared in-memory behavior models. It does not edit production code, push branches, merge pull requests, publish releases, access secrets, or claim exhaustive fault detection.
