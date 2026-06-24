# OAK + Bayes-Tristan Verification Protocol

**Status:** executable research-governance scaffold.  
**Goal:** separate vision, definition, conjecture, prototype, evidence, proof and canonization.

---

## 1. Core rule

```text
Fertile != true.
Tested != proved.
Proved != useful.
Useful != safe.
Canon = verified + useful + reusable + residue-audited.
```

OAK is the immune system. Bayes-Tristan is the prioritization engine.

---

## 2. Claim object

Every claim is represented as:

```yaml
claim:
  id: string
  title: string
  statement: string
  branch: string
  status: OAK-0..OAK-10
  hypotheses: []
  definitions: []
  invariants: []
  evidence_positive: []
  evidence_negative: []
  tests: []
  proof_status: none|sketch|partial|complete|refuted
  residue: []
  next_action: string
```

Mathematical form:

```math
c=(s,H,D,I,E^+,E^-,T,P,R,A)
```

where `s` is the statement, `H` hypotheses, `D` definitions, `I` invariants, `E+` supports, `E-` objections, `T` tests, `P` proof state, `R` residue, and `A` next action.

---

## 3. OAK levels

| Level | Name | Gate |
|---|---|---|
| OAK-0 | intuition | meaningful idea, not formalized |
| OAK-1 | definition | objects and terms defined |
| OAK-2 | conjecture | explicit statement + hypotheses |
| OAK-3 | prototype | executable test or model |
| OAK-4 | weak validation | examples and sanity checks pass |
| OAK-5 | robust validation | baselines, repeats, ablations, counterexample search |
| OAK-6 | partial proof | rigorous proof in subcases or supporting lemmas |
| OAK-7 | full proof | complete proof under stated hypotheses |
| OAK-8 | local canon | integrated into one branch |
| OAK-9 | reusable canon | used across branches |
| OAK-10 | foundational kernel | essential to the ecosystem |

---

## 4. Bayes-Tristan vector

For hypothesis `h`:

```math
B_T(h)=(P,U,F,T,C,R,S)
```

| Symbol | Meaning | Range |
|---|---|---|
| `P` | confidence/probability proxy | 0..1 |
| `U` | utility | 0..1 |
| `F` | fertility | 0..1 |
| `T` | testability | 0..1 |
| `C` | compressibility | 0..1 |
| `R` | risk/residue/illusion | 0..1 |
| `S` | OAK maturity normalized | 0..1 |

Action score:

```math
A(h)=0.22P+0.18U+0.18F+0.16T+0.12C+0.14S-0.25R.
```

This is not a truth metric. It is a research-action metric.

---

## 5. Promotion rules

### OAK-0 -> OAK-1

Required:

- name;
- definition attempt;
- at least one object example;
- at least one non-example or limitation.

### OAK-1 -> OAK-2

Required:

- explicit conjecture or theorem statement;
- hypotheses;
- predicted invariant or measurable output;
- known possible failure modes.

### OAK-2 -> OAK-3

Required:

- executable prototype, symbolic check, numerical experiment or formal proof skeleton;
- input/output specification;
- baseline or trivial case.

### OAK-3 -> OAK-4

Required:

- tests pass on examples;
- at least one counterexample search;
- limitations documented.

### OAK-4 -> OAK-5

Required:

- baseline comparison;
- ablation or control;
- repeated runs or independent examples;
- negative memory updated.

### OAK-5 -> OAK-6/OAK-7

Required:

- proof dependencies mapped;
- lemmas stated;
- edge cases handled;
- no hidden circularity.

---

## 6. Negative memory

Every failed claim should be stored as:

```yaml
negative_memory:
  id: string
  failed_claim: string
  failure_type: bad_definition|false_conjecture|bad_generalization|numerical_artifact|proof_gap|unsafe_leap
  counterexample: string
  lesson: string
  forbidden_pattern: string
  replacement_rule: string
```

Mathematical contraction:

```math
\mathcal M^-_t\subseteq\mathcal M^-_{t+1}\Rightarrow A_{t+1}\subseteq A_t
```

where `A_t` is the set of allowed proof/prototype paths after filtering known anti-patterns.

---

## 7. Residue audit

For every compression:

```math
R_X=X-\operatorname{EXP}(\operatorname{LOG}(X))
```

Audit:

1. Is `R_X` small in norm?
2. Is it structured?
3. Does it persist across methods?
4. Does it contain a topological/spectral/algebraic signature?
5. Does it point to a missing invariant?
6. Does it refute the compression?

Residue classification:

```text
noise | edge-case | missing invariant | counterexample | new branch | measurement artifact
```

---

## 8. Proof hygiene

Every proof candidate requires:

```text
axioms -> definitions -> lemmas -> theorem -> proof -> dependency graph -> edge cases -> counterexample search
```

Reject or downgrade if:

- an undefined term appears;
- a circular dependency appears;
- a non-equivalent analogy is used as proof;
- a numerical example is treated as universal;
- hypotheses are silently strengthened;
- non-commutative/non-associative products are used without order/parentheses.

---

## 9. Prototype hygiene

Every prototype requires:

```text
input spec + output spec + baseline + tests + failure cases + OAK status
```

A prototype result is promoted only if:

```math
score_{Tristan}-score_{baseline}>\epsilon
```

across controlled cases.

---

## 10. Canonization formula

```math
Canon(h)=1
```

only if:

```math
P+U+F+T+C+S-R-Cost-Illusion>\theta
```

and one of:

```text
OAK >= 5 for robust prototype canon
OAK >= 7 for theorem canon
OAK >= 8 for local reusable canon
```

---

## 11. Recommended next action selector

Choose next action by maximum expected gain:

```math
h^*=\arg\max_h \frac{\mathbb E[\Delta P+\Delta U+\Delta F+\Delta T-\Delta R]}{1+Cost(h)}.
```

Practical action labels:

```text
formalize_definition
write_theorem
search_counterexample
build_prototype
run_baseline
extract_invariant
audit_residue
write_negative_memory
promote_to_canon
demote_or_refute
```

---

## 12. Default OAK policy for Tristan branches

| Branch | Default status | Next OAK move |
|---|---|---|
| HGFM | OAK-1/2 | formal schemas + graph prototype |
| CVCD | OAK-1/2 | define invariants/residues + reconstruction tests |
| LOG/EXP | OAK-1/2 | connect to compression/Galois examples |
| Bayes-Tristan | OAK-1/3 | implement scoring and action ranking |
| FFWT-HAC-CVCD | OAK-2/3 | benchmark signal datasets |
| PrimeTensor | OAK-2/3 | arithmetic feature extraction tests |
| AlgebraDefectLab | OAK-2/3 | implement commutator/associator feature engine |
| HyperProof | OAK-1/3 | proof dependency graph prototype |
| ResidueTopology | OAK-2/3 | persistent-homology residue experiments |

---

## 13. Final rule

> Maximal generation is allowed only when maximal residue tracking is active.
