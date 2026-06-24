# Executable Core — Ω-ST Sciences de Tristan

This document describes the first executable layer added to the `Ω-ST` canon. It turns the manifesto into minimal Python objects that can be tested, ranked, reviewed and extended.

## Goal

The executable core makes the research loop machine-readable:

```text
science_card -> Bayes-Tristan score -> AIT-OAK review -> next action -> test -> memory -> canon
```

It deliberately starts small and auditable. The goal is not to pretend the weights or heuristics are final; the goal is to make them testable.

## Package

```text
sage_tristan/sciences_tristan/
  __init__.py
  science_card.py
  bayes_tristan_engine.py
  ait_oak.py
```

## Core objects

### `ScienceCard`

Canonical representation of an idea, hypothesis, theory, prototype, residue, memory item or agent.

Key fields:

- `id`
- `name`
- `kind`
- `branch`
- `statement`
- `status_oak`
- `bayes_tristan`
- `assumptions`
- `predictions`
- `baselines`
- `tests`
- `positive_memory`
- `negative_memory`
- `residues`
- `next_actions`

### `BayesTristanVector`

Separates axes that are often confused:

```text
true, useful, fertile, testable, safe, compressible, novel, valuable
```

This is the core scientific hygiene rule: high fertility does not imply high truth.

### `BayesTristanEngine`

Ranks a portfolio of cards and identifies:

- top-priority cards;
- OAK gaps;
- branch distribution;
- status distribution;
- next actions.

### `AITOAK`

First-pass review engine that generates:

- safe wording;
- strengths;
- risks;
- baselines;
- suggested tests;
- falsifiers;
- next action.

It is a hygiene engine, not a proof engine.

## Minimal example

```python
from sage_tristan.sciences_tristan import AITOAK, BayesTristanEngine, ScienceCard

card = ScienceCard.from_mapping({
    "id": "ST-H-1000",
    "name": "FFWT-HAC-CVCD signal invariants",
    "kind": "hypothesis",
    "branch": "ffwt_hac_cvcd",
    "statement": "A candidate multi-scale signal pipeline may improve anomaly detection.",
    "status_oak": "Omega_2",
    "bayes_tristan": {
        "true": 0.55,
        "useful": 0.90,
        "fertile": 0.95,
        "testable": 0.90,
        "safe": 0.95,
        "compressible": 0.80,
        "novel": 0.75,
        "valuable": 0.85,
    },
    "next_actions": ["Run a baseline comparison against FFT and wavelets."],
})

engine = BayesTristanEngine([card])
print(engine.portfolio_report())

review = AITOAK().review(card)
print(review.as_dict())
```

## Tests

The minimal tests live in:

```text
tests/test_sciences_tristan_core.py
```

They check that:

- priorities stay normalized;
- Bayes-Tristan ranks stronger cards above weaker cards;
- AIT-OAK produces tests and falsifiers.

Run with:

```bash
python -m pytest tests/test_sciences_tristan_core.py
```

## OAK limits

Current status: `Omega_3 scaffold`.

This code is a prototype skeleton. It should not yet be treated as a calibrated scientific decision engine. It becomes stronger only after:

1. more science cards are added;
2. weight sensitivity is tested;
3. rankings are compared to human review;
4. false promotions are stored in memory-negative;
5. prototype outcomes are fed back into scores.

## Next implementation steps

1. Add a CLI: `python -m sage_tristan.sciences_tristan rank examples/sciences_tristan_seed.yaml`.
2. Add JSON/YAML export of AIT-OAK reviews.
3. Add weight profiles for different research modes: exploratory, publication, prototype, revenue, safety.
4. Add memory-negative updates after failed tests.
5. Connect `ffwt_hac_cvcd` and `fractal_rlc_lab` prototypes to automatic card updates.
