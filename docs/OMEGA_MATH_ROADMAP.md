# Ω-MATH-TRISTAN Roadmap

**Status:** strategic roadmap for formalization, prototypes, tests and canon promotion.

---

## Phase 0 — Corpus stabilization

Goal: turn raw ideas into navigable, non-ambiguous artifacts.

Deliverables:

- `docs/OMEGA_MATH_TRISTAN_CANON.md`
- OAK status table
- theory cards
- branch registry
- negative-memory registry
- glossary of symbols

Definition of done:

```text
Every named object has a definition, status, assumptions and next action.
```

---

## Phase 1 — Executable core

Goal: create the minimal engine that can score, classify and promote ideas.

Modules:

| Module | Purpose |
|---|---|
| `omega_math_tristan.py` | claim/status/scoring utilities |
| `prime_tensors.py` | primorial residue and gap tensor extraction |
| `algebra_defect_lab.py` | commutator/associator/defect features |
| `hgfm.py` | hypergraph node/edge representation |
| `bayes_tristan.py` | hypothesis action scoring |
| `negative_memory.py` | anti-pattern registry |

Definition of done:

```text
pytest passes and each module has at least one executable example.
```

---

## Phase 2 — Mathematical formalization

Goal: separate theorem, conjecture and prototype layers.

Artifacts:

1. theorem bank;
2. conjecture bank;
3. proof dependency graphs;
4. counterexample search notes;
5. formal status tags.

Highest-priority theorem families:

- commutator/associator invariance;
- spectral invariance;
- negative-memory contraction;
- LOG/EXP closure under Galois conditions;
- prime residue non-nullity;
- periodic dynamics block reduction;
- approximation error monotonicity.

---

## Phase 3 — Prototype laboratories

### Lab A — PrimeTensor

Inputs:

```text
N primes, max gap offset k, feature maps phi
```

Outputs:

```text
residue signatures, gap tensors, compression scores, anomaly reports
```

OAK gate:

```text
Patterns must be compared against randomized or baseline sequences.
```

### Lab B — AlgebraDefectLab

Inputs:

```text
algebra multiplication table or sampled operations
```

Outputs:

```text
commutator norm, associator norm, norm defect, zero-divisor candidates
```

OAK gate:

```text
Non-commutative/non-associative behavior must be explicitly ordered and parenthesized.
```

### Lab C — FFWT-HAC-CVCD

Inputs:

```text
signals/images/spectra, algebra choice, wavelet/fractal transform parameters
```

Outputs:

```text
multi-scale covariance, hypercoherence, feature vector, baseline comparison
```

OAK gate:

```text
No performance claim without baseline and validation split.
```

### Lab D — ResidueTopology

Inputs:

```text
original object X, reconstruction X_hat, residual R
```

Outputs:

```text
norm, spectral residue, persistent topology, missing-invariant candidates
```

OAK gate:

```text
Structured residuals must be distinguished from preprocessing artifacts.
```

### Lab E — HyperProof

Inputs:

```text
axioms, definitions, lemmas, theorem, proof steps
```

Outputs:

```text
proof hypergraph, dependency graph, circularity risk, missing lemma candidates
```

OAK gate:

```text
Any proof with an undefined term or hidden circularity is downgraded.
```

---

## Phase 4 — Canon publication packages

Each branch gets a DCT++ packet:

```yaml
document: formal explanation
code: executable prototype
test: pytest/baseline/counterexample search
data: examples or generated fixtures
risk: limitations and failure modes
ethics: safe use and claim boundaries
status: OAK level
next: next action
links: related branches
```

Promotion target:

```text
OAK-5 for prototype branches, OAK-7 for theorem branches.
```

---

## Phase 5 — Mycelial integration

Goal: unify branches into an HGFM graph.

Node types:

```text
definition, theorem, conjecture, prototype, test, dataset, counterexample, residue, artifact, branch
```

Edge types:

```text
defines, proves, tests, refutes, generalizes, compresses, expands, depends_on, blocks, promotes
```

Metric:

```math
FertilityDensity(T)=\frac{validated\_outputs(T)}{complexity(T)+1+negative\_memory(T)}.
```

---

## Phase 6 — Research engine

Goal: turn the canon into an active research system.

Loop:

```text
claim -> OAK status -> Bayes-Tristan score -> next action -> artifact -> tests -> memory update -> promotion/demotion
```

Potential automation:

- generate claim cards;
- run tests;
- compare baselines;
- update OAK status;
- write negative-memory entries;
- create reports;
- rank next actions.

---

## Priority ranking

| Rank | Branch | Why |
|---|---|---|
| 1 | FFWT-HAC-CVCD | strongest experimental payoff |
| 2 | Bayes-Tristan/OAK | controls the whole canon |
| 3 | PrimeTensor/GapTensor | easy to prototype and visualize |
| 4 | AlgebraDefectLab | original, measurable, reusable |
| 5 | HGFM | organizes all branches |
| 6 | HyperProof | proof hygiene and anti-illusion |
| 7 | ResidueTopology | missing-invariant discovery |
| 8 | LOG/EXP theory | conceptual backbone |

---

## Long-term vision

```text
A living mathematical forest:
roots = axioms and definitions
trunk = HGFM + CVCD + OAK + Bayes-Tristan
branches = arithmetic, algebra, topology, signal, proof, AI
leaves = examples, tests, datasets, simulations
fruits = prototypes, theorems, papers, tools
seeds = new theories generated by EXP
soil = M+ and M- memory
```

---

## Non-negotiable rule

> The system may generate boldly, but it must certify conservatively.
