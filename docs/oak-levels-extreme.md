# OAK Levels Extreme

OAK is the validation tribunal for TFUGA / SAGE-TRISTAN. It classifies every idea, claim, module, artifact, and prototype by its distance to verifiable canon.

## Core rule

```text
Vision is allowed.
Speculation is allowed.
Ambition is allowed.
But promotion requires definition, tests, evidence, limits, and memory of failure.
```

## OAK ladder

| Level | Name | Required evidence | Promotion condition |
|---|---|---|---|
| OAK-0 | Raw intuition | none | named idea with scope |
| OAK-1 | Definition | terms, boundaries, risks | clear object and forbidden overclaims |
| OAK-2 | Formalization | equations, schemas, pseudo-code | falsifiable claims and expected residues |
| OAK-3 | Simulation | reproducible numerical behavior | runnable experiment or notebook |
| OAK-4 | Prototype | executable implementation | tests pass and outputs are saved |
| OAK-5 | Benchmark | comparison to baseline | explicit metric and result table |
| OAK-6 | Local validation | robustness on defined domain | repeated results and failure modes recorded |
| OAK-7 | Canon | stable, reusable, documented | accepted as core module |
| OAK-8 | Publication grade | proof or strong empirical report | article, whitepaper, or peer-grade note |
| OAK-9 | Generative canon | generates other validated modules | produces validated descendants |

## OAKScore

```text
OAKScore =
  0.18 * coherence
+ 0.18 * testability
+ 0.16 * reproducibility
+ 0.14 * gain_vs_baseline
+ 0.12 * compression
+ 0.10 * fertility
+ 0.07 * safety
+ 0.05 * utility
```

## Verdicts

| Verdict | Meaning | Required action |
|---|---|---|
| ACCEPT | promote | add to canon and link evidence |
| HOLD | promising but incomplete | define missing pieces |
| TEST | needs experiment | create benchmark or notebook |
| SPLIT | too broad | divide into smaller modules |
| MERGE | duplicate or coupled | integrate with nearest module |
| REJECT | unsupported or wrong | document why |
| M_MINUS | useful failure | archive as negative memory |

## Mandatory OAK questions

1. What is the exact claim?
2. What would falsify it?
3. What is the simplest baseline?
4. What is the measurable residue?
5. What is the current truth layer?
6. What is the strongest counterexample known?
7. What is the smallest prototype?
8. What belongs in M_MINUS?

## Anti-overclaim policy

Forbidden promotions:

```text
T0/T1 idea → treated as proven theory
simulation → treated as physical measurement
beautiful equation → treated as truth
single good result → treated as robust validation
sedenion/octonion output → treated as meaningful without projection and defect metrics
```

Safe language:

```text
exploratory framework
candidate invariant
prototype-level result
local validation
hypothesis generator
benchmark candidate
```

Unsafe language unless proven:

```text
new law of physics
universal proof
always improves
solves all cases
validated everywhere
```
