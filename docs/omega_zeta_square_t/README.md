# Ω-ZETA-SQUARE-T∞ / Ω-RH-PROOF-OS-T∞

Status: `research-toolkit`, `no-RH-solution-claimed`.

## Canonical coordinate

Center the functional equation at one half:

\[
w=s-\frac12,
\qquad
u=w^2=(s-\tfrac12)^2.
\]

For a candidate zero \(\rho=\beta+i\gamma\), define

\[
\delta=\beta-\frac12,
\qquad
u=(\delta+i\gamma)^2
=\delta^2-\gamma^2+2i\delta\gamma.
\]

Hence

\[
\delta^2=\frac{|u|+\Re u}{2},
\qquad
\gamma^2=\frac{|u|-\Re u}{2}.
\]

The exact centered critical-line defect is therefore

\[
D_{RH}(u)=\frac{|u|+\Re u}{2}=(\beta-\tfrac12)^2.
\]

This identity is a coordinate reformulation, not a proof of RH.

## Quotient geometry

The completed Riemann function obeys \(\xi(s)=\xi(1-s)\). After centering,
this becomes \(w\leftrightarrow-w\). The invariant polynomial coordinate for
this \(\mathbb Z_2\) symmetry is \(u=w^2\).

Consequences:

- the critical line \(\Re s=1/2\) maps to \(\mathbb R_-\);
- the centered real axis maps to \(\mathbb R_+\);
- both strip boundaries \(\Re s=0\) and \(\Re s=1\) collapse to
  \(x=1/4-y^2\);
- the critical strip maps to \(x\le 1/4-y^2\);
- a functional pair \(s\) and \(1-s\) has the same square image.

For trivial zeros \(s=-2n\), the same centered square gives

\[
u_n^{triv}=(2n+\tfrac12)^2>0.
\]

Under RH, non-trivial zeros \(1/2\pm i\gamma_n\) map to

\[
u_n^{nt}=-\gamma_n^2<0.
\]

## Entire non-trivial sector

Define the standard completed function

\[
\xi(s)=\frac12s(s-1)\pi^{-s/2}\Gamma(s/2)\zeta(s).
\]

Because \(\xi(1/2+w)\) is even in \(w\), the branch-independent function

\[
\Theta(u)=\xi\!\left(\frac12+\sqrt u\right)
\]

is entire. The known criterion is:

\[
RH\iff Z(\Theta)\subset\mathbb R_-.
\]

This criterion is not claimed as new in this repository.

## Unified zeta-square object

A branch-independent object carrying centered-square images of all zeta zeros is

\[
\mathcal Z_\square(u)=
(u-\tfrac14)
\zeta(\tfrac12+\sqrt u)
\zeta(\tfrac12-\sqrt u).
\]

The factor \(u-1/4\) removes the pole pair after quotienting. The package exposes
numerical evaluation away from the removable point \(u=1/4\), but certified
analysis should use an analytic continuation rather than direct cancellation.

## Stieltjes / moment axis

If RH holds and the non-trivial ordinates are \(\gamma_n>0\), then formally

\[
\frac{\Theta'(u)}{\Theta(u)}
=\sum_n\frac{1}{u+\gamma_n^2}.
\]

This motivates inverse-even moments

\[
p_k=\sum_n\gamma_n^{-2k}
\]

and Stieltjes/Hankel positivity tests. The implementation currently provides only
**finite-sample numerical diagnostics**. Every report contains
`proves_rh = False` by construction.

## Parabolic tomography

Move the center vertically:

\[
c_b=\frac12+ib,
\qquad
u_b=(\rho-c_b)^2.
\]

Then

\[
u_b=\delta^2-(\gamma-b)^2+2i\delta(\gamma-b).
\]

For \(\delta=0\), the full trajectory remains on \(\mathbb R_-\). For
\(\delta\ne0\), eliminating \(b\) gives

\[
\Re u=\delta^2-\frac{(\Im u)^2}{4\delta^2},
\]

with vertex \(\delta^2=D_{RH}\). This is a geometric diagnostic and a source of
candidate lemmas, not a proof mechanism by itself.

## Integration with Tristan systems

This branch is intended to connect to:

- **HGFM** — graph criteria, implications, dependencies and counterexamples;
- **CVCD** — search for minimal invariant sets forcing spectral reality;
- **LOG/EXP / CDIC-T** — translate zeros ↔ moments ↔ operators ↔ inequalities;
- **TensorProdLift-T** — lift polynomial moment/Hankel constraints;
- **FFWT-HAC-CVCD** — conjecture generation from multi-scale numerical structure;
- **Bayes-Tristan** — rank research paths by fertility/testability, not truth probability;
- **UNC²-T** — track numerical, symbolic, bibliographic and inference uncertainty;
- **M⁻** — retain failed RH pathways and anti-patterns;
- **AIT/SAGE** — synthesize bounded lemmas and attack them adversarially;
- **OAK** — block false promotion from reformulation or finite verification to proof.

## OAK contract

Allowed statuses include `OBSERVED`, `NUMERICALLY_VERIFIED`,
`SYMBOLICALLY_DERIVED`, `KNOWN_THEOREM`, `CONJECTURE`, `PROVED`, and `REFUTED`.

Forbidden patterns include:

1. finite verification → universal RH claim;
2. numerical fit → exact identity;
3. equivalent reformulation → claimed solution;
4. operator reconstructed from known zeros → independent Hilbert–Pólya solution;
5. conjectural dependency inside a `PROVED` claim;
6. branch-cut or cancellation numerics presented as analytic continuation;
7. pattern detection presented as theorem.

A true proof path must terminate entirely in proof-grade leaves (`PROVED` or
`KNOWN_THEOREM`) with all quantifiers and domains preserved.

## Current executable surface

```python
from omega_zeta_square_t import nontrivial_zero_image, rh_defect

u = nontrivial_zero_image(0.6, 21.0)
assert abs(rh_defect(u) - 0.01) < 1e-12
```

Finite moment diagnostics:

```python
from omega_zeta_square_t import finite_stieltjes_report

report = finite_stieltjes_report([14.1347251417, 21.0220396388], hankel_size=1)
assert report.proves_rh is False
```

## Next proof-engine increments

1. central-derivative engine for \(\xi^{(2k)}(1/2)\);
2. coefficient-to-moment symbolic conversion;
3. exact/rational-arbitrary-precision Hankel certificates;
4. Padé/Stieltjes continued-fraction layer;
5. Jacobi reconstruction from moments;
6. HGFM implication graph linking every criterion and proof obligation;
7. CVCD criterion compressor;
8. adversarial M⁻ generator for false RH arguments;
9. bibliography/provenance ledger distinguishing known criteria from Tristan combinations;
10. CI OAK receipt showing exactly what was tested and what remains unproved.
