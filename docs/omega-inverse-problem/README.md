# Ω-INVERSE-PROBLEM-T∞ R0.1

Status: executable OAK-safe research prototype candidate.

Ω-INVERSE-PROBLEM-T∞ generalizes Ω-INVERSE-T∞ from local analytic function reversion to a broader class of inverse problems.

## Mother problem

The forward model is

\[
y = F(x;\theta)+\varepsilon.
\]

The inverse task is not assumed to be a globally single-valued function. The output can instead be a local inverse, a minimum-norm representative, a regularized reconstruction, a posterior distribution, or a branch-aware nonlinear solution.

```text
forward model
    -> structural analysis
    -> rank / conditioning / branch gate
    -> inverse representation router
    -> candidate reconstruction
    -> forward check
    -> uncertainty + warnings
    -> OAK evidence
```

## Implemented R0.1

### 1. Spectral identifiability gate

For a linear map `y = A x`, the reference kernel estimates singular values from a **small Gram matrix**:

\[
G=\begin{cases}
A^TA,&m\ge n,\\
AA^T,&m<n.
\end{cases}
\]

A stdlib-only Jacobi symmetric eigensolver then reports:

- row/column dimensions;
- numerical rank;
- nullity and left nullity;
- singular spectrum;
- nonzero-subspace condition number;
- full-row-rank/full-column-rank flags.

Using the smaller Gram avoids introducing structural zero modes merely because a matrix is wide or tall.

Because forming a Gram matrix squares the condition number, R0.1 also enforces a numerical resolution floor proportional to `sqrt(machine epsilon)`. Modes below that floor are treated as numerical null modes instead of being inverted.

### 2. Moore–Penrose inverse

For `m >= n`, R0.1 uses

\[
A^+=(A^TA)^+A^T.
\]

For `m < n`, it uses

\[
A^+=A^T(AA^T)^+.
\]

The spectral pseudoinverse of the symmetric Gram matrix is constructed from its eigenvectors and retained eigenvalues.

The router distinguishes:

- square full-rank maps;
- overdetermined full-column-rank maps;
- underdetermined full-row-rank maps;
- rank-deficient maps.

For non-unique systems the returned Moore–Penrose solution is the minimum-norm representative. It is not called the unique physical solution.

### 3. Tikhonov reconstruction

The regularized objective is

\[
\min_x \|Ax-y\|_2^2+\lambda\|x-x_{prior}\|_2^2.
\]

R0.1 solves

\[
(A^TA+\lambda I)x=A^Ty+\lambda x_{prior}.
\]

Regularization is treated as an explicit modeling assumption, not a proof-enhancing operation.

### 4. Nonlinear inverse solver

For nonlinear `F(x)`, the prototype performs a finite-difference Jacobian step with Levenberg/Tikhonov damping and residual-decreasing backtracking:

\[
\Delta x \approx (J^TJ+\lambda I)^{-1}J^T(y-F(x)).
\]

The solver records residual history and does not claim global convergence or branch uniqueness.

### 5. Linear-Gaussian Bayesian inverse

For

\[
x\sim \mathcal N(\mu_0,C_0),\qquad
y|x\sim\mathcal N(Ax,R),
\]

R0.1 computes

\[
C_{post}^{-1}=C_0^{-1}+A^TR^{-1}A
\]

and

\[
\mu_{post}=C_{post}(C_0^{-1}\mu_0+A^TR^{-1}y).
\]

The posterior is conditional on the declared prior and noise model.

### 6. Forward↔inverse cycle checks

For linear systems, the kernel records both forward and inverse cycle residuals. In a null-space direction, a perfect forward reconstruction can coexist with imperfect recovery of the original state; this is expected ambiguity, not automatically a solver bug.

## Independent NumPy baseline

The runtime remains standard-library-only, but CI installs NumPy **only as an external baseline**.

`tests/test_omega_inverse_problem_numpy_baseline.py` compares the reference Moore–Penrose implementation against `numpy.linalg.pinv` on:

- square matrices;
- overdetermined matrices;
- underdetermined matrices;
- multiple deterministic random families;
- explicit rank-deficient matrices.

This baseline exposed and forced the correction from a universal `A^T A` path to the current small-Gram geometry. The failed design is retained conceptually as M⁻ evidence: a mathematically valid identity can still be a poor finite-precision implementation.

## Reference presets

```bash
python -m omega_inverse_problem_t.cli --preset sensor-overdetermined
python -m omega_inverse_problem_t.cli --preset design-underdetermined
python -m omega_inverse_problem_t.cli --preset ill-conditioned
python -m omega_inverse_problem_t.cli --preset bayes-scalar
python -m omega_inverse_problem_t.cli --preset nonlinear-calibration
```

Reports can be persisted as JSON and Markdown.

## Domain interpretations

| Forward model | Inverse interpretation |
|---|---|
| sensor state -> voltages | calibration / state estimation |
| parameters -> experimental response | parameter identification |
| circuit values -> impedance spectrum | component reconstruction |
| design -> simulated performance | inverse design |
| latent state -> observation | state reconstruction |
| source -> field / temperature / wave | source localization |
| material composition -> spectrum | spectral unmixing |
| command -> state transition | local control inversion |
| encoder -> compressed representation | decoder/reconstruction |

## Relation to Ω-INVERSE-T∞

Ω-INVERSE-T∞ remains the analytic/local branch engine:

```text
Taylor jet -> Taylor/Puiseux inverse jet -> branch/reconstruction evidence
```

Ω-INVERSE-PROBLEM-T∞ sits above it:

```text
problem geometry
 -> exact/local analytic inverse when available
 -> Moore-Penrose / regularized / nonlinear / Bayesian inverse otherwise
```

The intended future router will use Ω-INVERSE-T∞ as one backend rather than replacing it.

## OAK boundaries

R0.1 deliberately separates:

1. **data fit** from physical truth;
2. **minimum-norm representative** from unique preimage;
3. **numerical rank** from exact symbolic rank;
4. **regularization** from evidence;
5. **posterior probability** from proof;
6. **local nonlinear convergence** from global uniqueness;
7. **condition-number diagnostics** from certified uncertainty bounds;
8. **Gram-based reference numerics** from a production-quality SVD.

The current Jacobi/Gram kernel is designed for small research examples and deterministic tests. It is not a replacement for LAPACK/SVD libraries on large or safety-critical systems.

## R0.2+ roadmap

- connect the existing Ω-INVERSE-T∞ Taylor/Puiseux compiler as a local predictor backend;
- expose null-space bases, observable/unobservable subspaces and resolution matrices;
- generalized Tikhonov `L` operators and L-curve/GCV selection experiments;
- robust losses for outliers;
- constraints: positivity, bounds, conservation and sparsity;
- automatic differentiation/Jacobian providers;
- Bayesian nonlinear Laplace approximation and sampling adapters;
- branch ensembles and multimodal posterior representation;
- design-inverse multi-objective optimization;
- identifiability maps across parameter space;
- uncertainty propagation and interval/ball certificates;
- domain adapters for circuits, sensors, spectra and dynamical systems;
- OAKBench performance/scaling baselines against recognized numerical libraries before any speed or robustness claim.
