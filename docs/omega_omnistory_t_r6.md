# Ω-OMNISTORY-T∞ R6

R6 generalizes the existing manga/anime stack into a regenerative, proof-carrying storyworld layer.

## Scope

R6 does **not** claim autonomous artistic quality, audience success, legal clearance, final animation, or commercial viability. It formalizes a deterministic software architecture for:

- one causal `StoryIR` shared by manga, anime, novel and game projections;
- typed character genomes, events and a versioned canon ledger;
- continuity validation and causal-cycle detection;
- a multi-scale narrative residual field;
- residual-to-generator proposals with `Generator != Judge` enforced;
- JIT generator coalitions by required outputs;
- meta-depth control: extra meta layers must pay for complexity and risk;
- explicit automation-value scoring;
- fail-closed crystallization decisions;
- BOOK0-based regeneration receipts with SHA-256 digests and capability closure.

## Architecture

```text
Intent / StoryWorld
  -> StoryIR
  -> Continuity + Canon checks
  -> ResidualField
  -> Generator Registry
  -> Candidate Improvement
  -> Frozen Benchmark
  -> OAK decision
  -> Crystal
  -> BOOK0 regeneration receipt
  -> Manga / Anime / Novel / Game projection
```

## Constitutional invariants

```text
Generated != Verified
Generated != Canon
Generator != Judge
SameCanon != SamePresentation
AudienceModel != Audience
MoreMeta != Better
MoreContent != MoreValue
```

## Meta loop

```text
GENERATE
-> CHECK
-> RESIDUALIZE
-> PROPOSE GENERATOR / IMPROVEMENT
-> BENCHMARK
-> ABLATE
-> PROMOTE | KEEP_EXPERIMENTAL | DEPRECATE | DESTROY
-> CRYSTALLIZE
-> REGENERATE
```

A deeper meta-layer is admissible only when:

```text
verified_gain > added_complexity + added_risk
```

This is a software governance heuristic, not a scientific law.

## Commands

```bash
python -m omega_omnistory_t validate-reference
python -m omega_omnistory_t projection manga
python -m omega_omnistory_t projection anime
python -m omega_omnistory_t meta-demo
python -m omega_omnistory_t regenerate-demo
pytest -q tests/test_omega_omnistory_t_r6.py
```

## BOOK0_MIN R6

The minimal regenerative nucleus stores:

- StoryIR schema reference;
- generator ABI (`plan/generate/verify/repair/compress/regenerate`);
- canon rules;
- OAK rules;
- rights rules;
- regeneration recipes;
- frozen benchmark IDs.

The objective is not byte-identical recreation of every generated asset. The measurable target is **capability regeneration closure**.

## Current epistemic status

```text
StoryIR / CanonLedger       FORMALIZED
Continuity / Causal checks  PROTOTYPED
ResidualField               PROTOTYPED
Meta-generator proposals    PROTOTYPED
Crystallization controller  PROTOTYPED
BOOK0 receipts              PROTOTYPED
Manga/anime projection      STRUCTURAL PLAN ONLY
Final audiovisual output    NOT VALIDATED
Audience quality            NOT VALIDATED
Commercial viability        NOT VALIDATED
Publication                 PRIVATE-DRAFT
```

R6 is intentionally a bounded next layer over the existing R0.1-R5 pipeline rather than a replacement for it.
