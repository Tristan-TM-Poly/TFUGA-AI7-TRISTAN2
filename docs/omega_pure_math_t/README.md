# Ω-PURE-MATH-T∞ — executable pure-mathematics research kernel

**Status:** R0.1 formalization scaffold.  
**Scope:** definitions, finite algorithms, proof skeletons, counterexample memory, OAK status separation.  
**Non-claim:** names, analogies and computational checks are not proofs of novelty or mathematical truth.

## Mother object

The working ten-slot theory object is

\[
\mathfrak T=
(\mathcal O,\mathcal M,\mathcal R,\mathcal G,\mathcal I,
\mathcal D,\mathcal F,\mathcal P,\mathcal C,\mathcal E),
\]

with objects, morphisms, representations, transformations/generators, invariants,
defects/obstructions, factorizations, proofs, complexity measures and extensions.

The executable core compresses the workflow to six operations:

\[
\mathscr U=\{\mathsf R,\mathsf T,\mathsf I,\mathsf D,\mathsf F,\mathsf P\}
\]

for **represent → transform → invariant → defect → factor → prove**.

## R0.1 executable crystals

### 1. Ω-BRACKET-SPECTRUM-T∞

Enumerates all full binary parenthesizations of an ordered finite sequence,
evaluates them under a supplied binary operation, extracts distinct values and
computes a metric diameter.

For \(n\) inputs the parenthesization count is Catalan \(C_{n-1}\).

The first executable theorem family is:

\[
A\text{ associative}\Longrightarrow
D_A(x_1,\ldots,x_n)=0.
\]

Conversely, zero triple defect for every triple is exactly associativity.

### 2. Ω-FACTOR-BRICKS-T∞

Factorization is relative to a declared language of bricks. A witness records

\[
X\simeq B_1\otimes\cdots\otimes B_k
\]

and its length. Concatenating witnesses gives the constructive basis of

\[
\ell_{\mathcal B}(X\otimes Y)
\le \ell_{\mathcal B}(X)+\ell_{\mathcal B}(Y).
\]

The implementation never labels an unknown object irreducible merely because no
factorization has been recorded.

### 3. Ω-INVARIANT-COMPILER-T∞ / Ω-CVCD-PURE-T∞

An `Invariant` stores an extractor and equivalence relation. If the invariant is
known to be preserved by admissible isomorphisms, differing values provide an
obstruction certificate.

`cvcd_matrix` computes

\[
D^P_{ij}=d(P(R_i(X)),P(R_j(X)))
\]

for explicit representations and an explicit metric.

### 4. Ω-NEGATIVE-MATH-T∞

`NegativeMathRegistry` stores failed hypotheses, counterexamples, exact reasons
for failure and repaired hypotheses. `minimal_sufficient_subsets` performs an
exact finite inclusion-minimal hypothesis search relative to a supplied proof
oracle.

### 5. Ω-STRUCTURAL-DNA-T∞

`StructuralDNA` records finite signatures for symmetries, invariants, defects,
factorizations, dimensions, duals, limits, representations and obstructions.
Fingerprints are canonicalized and hashable. A collision is **not** an
isomorphism proof: it is a signal that the current signature may be incomplete.

### 6. Ω-MATHEMATICAL-COMPILER-T∞

Every named definition can be expanded into twelve standard research questions:

1. existence;
2. uniqueness;
3. closure;
4. invariance;
5. stability;
6. factorization;
7. classification;
8. extremum;
9. duality;
10. local-global;
11. approximation;
12. obstruction.

The mutation axes are finite↔infinite, discrete↔continuous,
linear↔nonlinear, commutative↔noncommutative,
associative↔nonassociative, exact↔approximate, local↔global,
object↔dual and construction↔obstruction.

## Candidate theorem ledger

| ID | Statement family | R0.1 status |
|---|---|---|
| T1 | brick-length subadditivity | theorem skeleton + executable certificate |
| T2 | bracket diameter / associativity | theorem skeleton + exhaustive finite checker |
| T3 | invariant obstruction | theorem skeleton + executable certificate |
| T4 | equivariant Tensor Spectrum classification | conjecture/program |
| T5 | minimal complete invariant basis | conjecture/program |
| T6 | residual tower convergence | conjecture/program |
| T7 | uniqueness of minimal representations | conjecture/program |
| T8 | robust zero tomography from sampled \(\log|f|\) | conjecture/program |
| T9 | HGFM renormalization dimension | conjecture/program |
| T10 | proof-library compression | conjecture/program |
| T11 | bracket-space geometry | conjecture/program |
| T12 | defect-spectrum classification | conjecture/program |

## CLI

```bash
python -m omega_pure_math_t protocol BracketSpectrum
python -m omega_pure_math_t bracket 10 3 2 --op sub
python -m omega_pure_math_t oak
```

## Validation

The R0.1 unit suite checks:

- Catalan counts \(1,2,5,14\);
- zero bracket diameter for addition;
- positive defect for subtraction;
- constructive T1 certificate;
- T3 invariant obstruction;
- CVCD symmetry under a symmetric metric;
- multiple minimal sufficient hypothesis sets;
- negative-math retrieval;
- canonical Structural DNA;
- 12-question protocol completeness;
- OAK theorem/conjecture separation.

## Existing repository integrations

This package is deliberately federating rather than duplicative:

- use `omega_logexp_morph_t` for matrix LOG/EXP, BCH, Magnus and generator calculus;
- use the existing HGFM/SAGE layers for repository-wide knowledge graphs;
- use OAK conventions to keep definitions, executable finite checks, conjectures
  and proved statements distinct;
- future R0.x work should connect Zero Tomography, Tensor Spectrum, proof
  geometry and HGFM renormalization through adapters rather than copy their
  underlying mathematics.

## Promotion rule

A branch is promoted only when it leaves behind:

```text
definition
+ hypotheses
+ example
+ counterexample or failure boundary
+ invariant/defect
+ executable test
+ proof or explicit conjecture status
+ baseline / prior-art comparison
```

The target is not maximal vocabulary. It is maximal **crystallization per concept**.
