# Ω-ROOTFLOW-T∞ R0.7 — Arbitrary Multiplicity Strata

R0.7 generalizes the R0.6 generic double-root collision manifold to a root of
arbitrary requested multiplicity `m >= 2`.

At a root `c` of exact multiplicity `m`,

\[
P(c)=P'(c)=\cdots=P^{(m-1)}(c)=0,
\qquad P^{(m)}(c)\neq0.
\]

For selected coefficient parameters `theta_j` multiplying monomials
`z^{k_j}`, differentiate every vanishing derivative constraint. For
`q=0,...,m-2`, the root-motion term vanishes because `P^{(q+1)}(c)=0`, leaving

\[
\sum_j (k_j)_q c^{k_j-q}\,d\theta_j=0,
\]

where `(k)_q` is the falling factorial. Thus

\[
A_{qj}=(k_j)_q c^{k_j-q},
\qquad T\Delta_m=\ker A.
\]

The final differentiated equation is

\[
P^{(m)}(c)\,dc+
\sum_j(k_j)_{m-1}c^{k_j-m+1}d\theta_j=0,
\]

so every tangent direction `v` induces

\[
\boxed{
 dc(v)=-\frac{\sum_j(k_j)_{m-1}c^{k_j-m+1}v_j}{P^{(m)}(c)}.
}
\]

R0.7 computes a deterministic RREF nullspace rather than using a black-box SVD
for the defining tangent basis.

## Canonical triple-root fixture

For

\[
P(z)=(z-1)^3=z^3-3z^2+3z-1
\]

at `c=1`, and coefficient degrees `(0,1,2,3)`, the constraint matrix is exactly

\[
A=
\begin{pmatrix}
1&1&1&1\\
0&1&2&3
\end{pmatrix}.
\]

It has rank 2, hence a two-dimensional complex tangent space in four selected
complex coefficient parameters. Since `P'''(1)=6`, root velocities along that
tangent space are finite and computable.

The finite-epsilon audit requires all constraints

\[
F,F',\ldots,F^{(m-1)}
\]

to have residual `O(epsilon^2)` under the first-order parameter/root predictor.

## Higher multiplicity refusal

If a user requests multiplicity `m` but `P^{(m)}(c)=0`, R0.7 refuses the model
with `OAK_REFUSE_MULTIPLICITY_HIGHER_THAN_REQUESTED`. This prevents a quadruple
root from being silently processed as a triple-root stratum.

## Exact rational multiplicity

R0.7 also adds exact multiplicity of a supplied rational root by repeated exact
division by `(z-c)` over `Fraction`. Examples:

- `(z-1)^3` at `c=1` -> multiplicity exactly 3;
- `(z-1)^4` at `c=1` -> multiplicity exactly 4;
- the same polynomial at `c=2` -> multiplicity exactly 0.

No numerical root solver is involved in those exact fixtures.

## CLI

```bash
python -m omega_rootflow_t exact-multiplicity \
  --coeffs=-1,3,-3,1 --root 1

python -m omega_rootflow_t multiplicity-tangent \
  --coeffs=-1,3,-3,1 \
  --critical-root 1 \
  --multiplicity 3 \
  --degrees 0,1,2,3 \
  --epsilon 0.001
```

## Version compatibility

The engine version advances to `R0.7`. Existing R0.1-R0.6 payload surfaces keep
their R0.6 payload schema version and now also expose `engine_version=R0.7`.
Only new R0.7 payload modes advertise schema `R0.7`. This avoids breaking
existing consumers solely because the engine gained new surfaces.

## OAK boundary

The derivative constraints are established local algebra. The implementation
claims no new theorem. RREF basis construction and finite-epsilon checks are
software procedures. The tangent space is complex unless a real parameter
constraint is explicitly imposed; real strata require realification of the
complex equations.
