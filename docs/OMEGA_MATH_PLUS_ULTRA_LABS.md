# Ω-MATH-TRISTAN PLUS ULTRA Labs

**Status:** OAK-1/OAK-3 executable laboratory expansion.  
**Purpose:** turn the canon into a concrete research engine: arithmetic tensors, algebraic defect features, HGFM routing, negative memory and residue-aware promotion.

---

## 1. The plus-ultra loop

```text
claim -> invariant extraction -> prototype -> baseline -> residue audit -> negative memory -> promotion or demotion
```

Mathematical control equation:

```math
\mathcal R_{n+1}=
\operatorname{Promote}_{OAK}
\left(
\operatorname{BayesT}
\left(
\operatorname{Test}
\left(
\operatorname{EXP}
\left(
\operatorname{CVCD}
\left(
\operatorname{LOG}(\mathcal R_n)
\right)
\right)
\right)
\right)
\right)
```

with a mandatory anti-illusion channel:

```math
\mathcal M^-_{n+1}=\mathcal M^-_n\cup\operatorname{Failures}(\mathcal R_n).
```

---

## 2. PrimeTensor Lab

### Object

For primes `p_i`, define:

```math
S_i=(p_i\bmod p_1,\dots,p_i\bmod p_{i-1}).
```

This is the residue signature of `p_i` relative to all earlier primes.

### Gap tensor

```math
G_{i,n}=p_{i+n}-p_i.
```

Feature vector:

```math
\Phi(G_{i,n})=(G_{i,n},G_{i,n}\bmod 2,G_{i,n}\bmod 3,\dots, G_{i,n}/\log(p_i+1)).
```

### OAK warning

A pattern in prime residues is not a proof about prime distribution. It is an experimental signature requiring baselines.

---

## 3. AlgebraDefectLab

### Object

A finite-dimensional algebra is represented by structure constants:

```math
e_i e_j=\sum_k c_{ijk}e_k.
```

Given vectors `x,y,z`, compute:

```math
[x,y]=xy-yx
```

```math
[x,y,z]=(xy)z-x(yz)
```

Norm defect:

```math
D_N(x,y)=\|xy\|-\|x\|\|y\|.
```

### OAK warning

In non-commutative systems, order matters. In non-associative systems, parentheses matter. Any prototype that hides order or parenthesization is downgraded.

---

## 4. HGFM Core Lab

### Node state

```math
s(v)=(p,u,f,t,c,r,o)
```

where:

- `p`: confidence;
- `u`: utility;
- `f`: fertility;
- `t`: testability;
- `c`: compressibility;
- `r`: residue/risk;
- `o`: OAK maturity.

### Edge types

```text
defines, proves, tests, refutes, generalizes, compresses, expands, depends_on, blocks, promotes
```

### Fertility density

```math
D_F(G)=\frac{\#validated\_outputs}{1+\#nodes+\#edges+\#negative\_motifs}.
```

---

## 5. NegativeMemory Lab

A negative-memory entry is:

```yaml
failure_type: proof_gap|bad_generalization|numerical_artifact|undefined_term|unsafe_claim
lesson: string
forbidden_pattern: string
replacement_rule: string
```

The purpose is not pessimism. It is immune memory.

```text
error -> anti-pattern -> replacement rule -> safer generator
```

---

## 6. Residue-aware promotion

A claim cannot be promoted if any of these are true:

1. undefined key term;
2. missing hypothesis;
3. no baseline for a performance claim;
4. no counterexample search for a conjecture;
5. structured residue ignored;
6. negative-memory conflict unresolved.

Promotion score:

```math
P_{canon}=\frac{P+U+F+T+C+S-R-I-Cost}{6}
```

where `I` is illusion/overclaiming penalty.

---

## 7. Executable files added by this lab layer

```text
sage_tristan/prime_tensors.py
sage_tristan/algebra_defect_lab.py
sage_tristan/hgfm_core.py
sage_tristan/negative_memory.py
examples/omega_math_lab_demo.py
tests/test_prime_tensors.py
tests/test_algebra_defect_lab.py
tests/test_hgfm_negative_memory.py
```

---

## 8. Research doctrine

> Revolutionary generation is allowed, but every generated claim must carry its OAK level, Bayes-Tristan vector, residue audit and negative-memory risk.

This keeps the ecosystem simultaneously ambitious and falsifiable.
