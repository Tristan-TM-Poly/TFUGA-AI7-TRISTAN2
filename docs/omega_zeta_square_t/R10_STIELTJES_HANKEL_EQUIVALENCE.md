# R10 — All-orders Stieltjes/Hankel equivalence

Status: `PROVED_DERIVED_CRITERION`, `PRIOR_ART_CLOSE`, `NOT_A_PROOF_OF_RH`.

R10 closes the analytic bridge drafted in R7. It derives an RH-equivalent
all-orders Stieltjes/Hankel criterion from standard entire-function
factorization, the centered-square function Theta, and the classical Stieltjes
moment theorem.

**Novelty is not claimed.** A literature search on 2026-08-11 found very recent
Polson preprints explicitly discussing Hankel/Jacobi positivity of secondary-zeta
moments as an RH-equivalent positivity face. Those works are recorded as prior
art and are not used as proof dependencies here.

## 1. General order-<1 lemma

Let `F` be a real entire function of order strictly less than one, with
`F(0) != 0`, and nonzero zeros `u_n`, repeated by multiplicity. Set

\[
\lambda_n=-\frac1{u_n}.
\]

Hadamard factorization gives a genus-zero product

\[
\frac{F(u)}{F(0)}=\prod_n\left(1+\lambda_nu\right).
\]

Because the exponent of convergence of the zeros is at most the order of `F`,

\[
\sum_n|\lambda_n|=\sum_n\frac1{|u_n|}<\infty.
\]

Also the zero set has no finite accumulation and avoids zero, so

\[
\Lambda:=\sup_n|\lambda_n|<\infty.
\]

The logarithmic derivative therefore has the locally normally convergent form

\[
L(u):=\frac{F'(u)}{F(u)}
=\sum_n\frac{\lambda_n}{1+\lambda_nu}.
\]

For `|u|<1/Lambda`, expand

\[
L(u)=\sum_{k=0}^{\infty}(-1)^k m_ku^k,
\qquad
m_k:=\sum_n\lambda_n^{k+1}.
\]

Every `m_k` converges absolutely. Since `F` is real entire, its zeros are closed
under conjugation, hence every `m_k` is real.

### Theorem

The following are equivalent:

1. every zero `u_n` of `F` is real and negative;
2. `(m_k)_{k>=0}` is a Stieltjes moment sequence;
3. for every `N>=1`, both Hankel families

\[
H_N^{(0)}=(m_{i+j})_{i,j=0}^{N-1},
\qquad
H_N^{(1)}=(m_{i+j+1})_{i,j=0}^{N-1}
\]

are positive semidefinite.

The equivalence of 2 and 3 is the classical Stieltjes moment theorem.

## 2. Negative-real zeros imply Stieltjes moments

If every `u_n<0`, then every

\[
\lambda_n=-1/u_n>0.
\]

Define the finite positive measure

\[
\mu=\sum_n\lambda_n\,\delta_{\lambda_n}.
\]

Its total mass is

\[
\mu([0,\infty))=\sum_n\lambda_n<\infty.
\]

Then

\[
\int_0^\infty t^k\,d\mu(t)
=\sum_n\lambda_n^{k+1}=m_k.
\]

Thus `(m_k)` is a Stieltjes moment sequence and all basic/shifted Hankel matrices
are PSD.

## 3. Stieltjes moments force negative-real zeros

Assume now that `(m_k)` is a Stieltjes moment sequence. There exists a positive
measure `mu` on `[0,infinity)` with

\[
m_k=\int_0^\infty t^k\,d\mu(t).
\]

From the original zero sums,

\[
0\le m_k
\le\sum_n|\lambda_n|^{k+1}
\le S\Lambda^k,
\qquad
S:=\sum_n|\lambda_n|.
\]

This forces the representing measure to be supported in `[0,Lambda]`. Indeed,
if for some `A>Lambda` one had `mu([A,infinity))=c>0`, then

\[
m_k\ge cA^k,
\]

contradicting `m_k<=S Lambda^k` for large `k`. Hence

\[
\operatorname{supp}\mu\subset[0,\Lambda].
\]

Define its Stieltjes transform in the same coordinate convention:

\[
G(u)=\int_{[0,\Lambda]}\frac{d\mu(t)}{1+tu}.
\]

It is holomorphic on

\[
\Omega=\mathbb C\setminus(-\infty,-1/\Lambda].
\]

Near zero,

\[
G(u)=\sum_{k=0}^{\infty}(-1)^km_ku^k=L(u).
\]

Thus `G` and `L=F'/F` agree in a neighborhood of zero. Continue this equality
along paths in the slit plane avoiding the discrete poles of `L`. If `L` had a
pole `u_*` inside `Omega`, choose a small disk around `u_*` containing no other
pole. Equality holds on the punctured disk, while `G` is holomorphic on the
whole disk. The singularity of `L` would therefore be removable, contradicting
that a zero of `F` gives a genuine logarithmic-derivative pole with positive
integer residue.

Consequently every pole of `L`, hence every zero of `F`, lies on

\[
(-\infty,-1/\Lambda]\subset\mathbb R_-.
\]

This proves 2 -> 1.

## 4. Apply the lemma to the centered-square Riemann function

Take

\[
F(u)=\Theta(u)=\xi\!\left(\frac12+\sqrt u\right).
\]

The source-bound known facts used here are:

- `Theta` is entire of order `1/2`;
- RH is equivalent to all zeros of `Theta` being negative real.

Therefore, with `u_n` the zeros of `Theta`, `lambda_n=-1/u_n`, and

\[
m_k=\sum_n\lambda_n^{k+1},
\]

we obtain the derived criterion

\[
\boxed{
RH
\iff
(m_k)_{k\ge0}\text{ is a Stieltjes moment sequence}
}
\]

and equivalently

\[
\boxed{
RH
\iff
H_N^{(0)}\succeq0\ \text{and}\ H_N^{(1)}\succeq0
\quad\text{for every }N\ge1.
}
\]

Under RH, `u_n=-gamma_n^2` and `lambda_n=gamma_n^{-2}`, so

\[
m_k=\sum_n\gamma_n^{-2k-2}.
\]

These are the shifted even secondary-zeta moments.

## 5. Finite-certificate corollary

The contrapositive is immediate:

\[
\boxed{
RH\text{ false}
\Longrightarrow
\exists N<\infty:
H_N^{(0)}\not\succeq0
\text{ or }
H_N^{(1)}\not\succeq0.
}
\]

Since a finite real symmetric matrix is PSD iff all of its principal minors are
nonnegative, RH failure implies the existence of a finite negative principal
minor, equivalently a finite negative quadratic witness.

This is an **existence theorem**. It does not provide an explicit universal
bound on the first failing order `N`. R5/R6/R8 remain valuable because they
model detection depth, while R9 gives a quantitative route for certifying a
specific finite witness against an infinite tail.

## 6. What R10 does not do

R10 is another criterion equivalent to RH, not a proof that its Hankel
conditions hold. In particular:

- no all-orders PSD claim has been established unconditionally;
- no finite computation can verify all orders;
- no novelty claim is made;
- recent 2026 prior art is conceptually close and requires full-text comparison;
- R9 tail bounds remain useful for explicit certificates even though R10 proves
  existential finite failure under RH falsity.

OAK status: `PROMOTE_DERIVED_EQUIVALENCE`, never `RH_SOLVED`.
