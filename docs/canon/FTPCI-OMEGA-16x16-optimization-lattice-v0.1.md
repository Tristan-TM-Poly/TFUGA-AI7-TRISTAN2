# FTPCI-Ω 16×16×… Optimization Lattice v0.1

**Statut OAK :** architecture de test et optimisation, pas revendication physique externe.  
**Rôle :** définir comment FTPCI-Ω explore, teste, compresse, décompresse et optimise les combinaisons de facteurs jusqu'à la limite théorique opérationnelle de l'Univers Tristan.

---

## 1. Idée centrale

FTPCI-Ω ne doit pas seulement produire une factorisation unique. Il doit produire un treillis de configurations :

```math
\mathcal L_{16^m}
=
\prod_{j=1}^{m}
\{0,1,2,\dots,15\}_j
```

Chaque axe possède 16 états propres, 16 choix, 16 modes ou 16 bandes.

Un point du treillis est :

```math
\ell=(i_1,i_2,\dots,i_m),\quad i_j\in\{0,\dots,15\}
```

Il représente une configuration candidate du système :

```text
compression × factorisation × OAK × fertilité × mémoire × décompression × prototype × codex × ...
```

---

## 2. Les 16 axes initiaux

Le premier lattice v0.1 utilise 16 axes :

1. `trace_quality`
2. `compression_depth`
3. `factor_rank`
4. `sparsity_level`
5. `invariant_preservation`
6. `oak_attack_strength`
7. `negative_memory_projection`
8. `fertility_threshold`
9. `decompression_depth`
10. `codex_depth_2n`
11. `prototype_minimality`
12. `residual_search_intensity`
13. `bridge_domain_count`
14. `anti_hype_threshold`
15. `reconstruction_tolerance`
16. `compute_budget`

Thus the initial search space is:

```math
16^{16}
```

But it must never be materialized densely.

---

## 3. JKD sparse rule

The dense lattice is only a conceptual upper bound.

Operational rule:

```math
Search(16^{16})\neq Enumerate(16^{16})
```

FTPCI-Ω must use:

- sparse sampling;
- beam search;
- Bayesian optimization;
- bandit selection;
- residual-guided exploration;
- negative-memory pruning;
- OAK rejection;
- fertility-gradient routing.

---

## 4. Objective function

The global objective is not maximum complexity. It is maximum verified fertility per cost.

```math
J(\ell)
=
\frac{
Fertility(\ell)\cdot OAK(\ell)\cdot Reuse(\ell)\cdot PrototypeValue(\ell)
}{
Cost(\ell)+Risk(\ell)+Hype(\ell)+Complexity(\ell)+1
}
```

Optimization target:

```math
\ell^* = \arg\max_{\ell\in\mathcal L_{16^m}} J(\ell)
```

---

## 5. Theoretical Tristan limit

The theoretical limit is not infinite compute. It is the best configuration reachable under constraints.

```math
\Omega_T(B)
=
\max_{\ell\in\mathcal L_{16^m}}
J(\ell)
\quad
\text{s.c.}\quad
Compute(\ell)\le B,
Traceable(\ell)=1,
OAKSafe(\ell)=1
```

where `B` is the available budget of compute, time, memory, attention, energy, and validation.

The Tristan limit is therefore:

```math
\Omega_T
=
\lim_{B\to B_{max}}
\Omega_T(B)
```

OAK interpretation: this is an operational optimum inside the architecture, not a claim about the physical universe.

---

## 6. Iterative compression/decompression loop

For each candidate lattice point:

```math
\mathcal T_{k+1}^{(\ell)}
=
\Pi_{safe}
Decompress_{\ell}
Select_{\Phi,OAK}
Compute_{\ell}
Factorize_{\ell}
Compress_{\ell}
(\mathcal T_k)
```

Then compare candidates:

```math
\ell_{k+1}
=
\arg\max_{\ell\in Beam_k}J(\ell)
```

Update memory:

```math
M^-_{k+1}=M^-_k+Failed(\ell)+Overhyped(\ell)+NonTraceable(\ell)
```

---

## 7. 16×16 local test matrix

Before scaling to 16 axes, every pair of axes must be tested as a 16×16 matrix.

For axes `a` and `b`:

```math
M_{ab}[i,j]=J(\ell\mid a=i,b=j)
```

This reveals:

- synergies;
- conflicts;
- ridges;
- dead zones;
- OAK-fail regions;
- fertility gradients.

Pairwise scan count:

```math
\binom{16}{2}\cdot 16^2=120\cdot256=30720
```

This is feasible as a first benchmark if each run is cheap.

---

## 8. Meta-synergy tensor

After pairwise matrices, build a synergy tensor:

```math
\mathcal S[a,b,i,j]
=
J(a=i,b=j)-J(a=i)-J(b=j)
```

If:

```math
\mathcal S[a,b,i,j]>0
```

then the combination is fertile.

If:

```math
\mathcal S[a,b,i,j]<0
```

then it is conflictual or redundant.

---

## 9. Negative-memory pruning

A failed region becomes forbidden or penalized:

```math
Penalty(\ell)=\lambda\cdot Sim(\ell,M^-)
```

Updated objective:

```math
J^-(\ell)=J(\ell)-Penalty(\ell)
```

Thus errors become geometry.

---

## 10. Decompression policy

A candidate is decompressed only if:

```math
J^-(\ell)>\theta_J
\land OAK(\ell)>\theta_O
\land Traceable(\ell)=1
```

Otherwise it stays compressed or goes to memory negative.

---

## 11. Required outputs per optimization cycle

Every 16×16×… cycle must produce:

1. best candidate `ell_star`;
2. top 16 configurations;
3. bottom 16 failure regions;
4. pairwise synergy matrices;
5. residual map;
6. memory-negative update;
7. one decompressed codex;
8. one prototype or test proposal;
9. OAK audit summary.

---

## 12. Minimal executable pseudocode

```text
axes = define_16_axes()
beam = seed_candidates(axes)
M_negative = load_negative_memory()

for cycle in range(N):
    candidates = expand_sparse_16x16(beam, axes)
    compressed = [compress(T, c) for c in candidates]
    factors = [factorize(z, c) for z, c in zip(compressed, candidates)]
    scores = [score_with_oak_and_fertility(g, c, M_negative) for g, c in zip(factors, candidates)]
    failures = select_failures(candidates, scores)
    M_negative.update(failures)
    beam = select_top16(candidates, scores)
    codex = decompress_best(beam[0])
    residual = compute_residual(T, codex)
    report(cycle, beam, failures, residual, M_negative)
```

---

## 13. Sceau canonique

```math
FTPCI\text{-}\Omega\text{-}16
=
Search_{sparse}(16^{m})
\rightarrow
Test_{16\times16}
\rightarrow
Score_{OAK,\Phi}
\rightarrow
Prune_{M^-}
\rightarrow
Decompress_{fertile}
\rightarrow
Optimize_{\Omega_T(B)}
```

**Résumé :** le système vise une limite théorique opérationnelle : la meilleure fertilité vérifiable atteignable sous contraintes, sans jamais matérialiser le treillis complet.