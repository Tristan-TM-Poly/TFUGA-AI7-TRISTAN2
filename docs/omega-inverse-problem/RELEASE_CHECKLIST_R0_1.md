# Ω-INVERSE-PROBLEM-T∞ R0.1 release checklist

## Structural analysis

- [x] singular-spectrum estimator implemented;
- [x] numerical rank and nullity exposed;
- [x] square / overdetermined / underdetermined / rank-deficient routing implemented;
- [x] small-Gram geometry selected by matrix shape;
- [x] sqrt(machine-epsilon) Gram precision floor implemented;
- [x] condition-number warning path implemented;
- [ ] scaling-policy sensitivity benchmark;
- [ ] explicit null-space basis export.

## Inverse backends

- [x] Moore–Penrose reference backend;
- [x] minimum-norm underdetermined reconstruction;
- [x] Tikhonov with optional prior center;
- [x] local damped Gauss-Newton with residual backtracking;
- [x] linear-Gaussian posterior mean/covariance;
- [ ] generalized regularization operator L;
- [ ] positivity/bounds/conservation constraints;
- [ ] robust-loss backend;
- [ ] nonlinear Bayesian backend.

## Evidence

- [x] square exact recovery reference;
- [x] overdetermined exact recovery reference;
- [x] underdetermined minimum-norm reference;
- [x] rank-deficient nullity reference;
- [x] Tikhonov closed-form identity reference;
- [x] prior-centered Tikhonov reference;
- [x] forward/inverse cycle-consistency reference;
- [x] nonlinear local reconstruction reference;
- [x] scalar Bayesian closed-form reference;
- [x] ill-conditioning diagnostic reference;
- [x] CLI JSON/Markdown reference generation;
- [x] deterministic NumPy `pinv` baseline suite added;
- [x] first exact-head core CI passed before NumPy hardening;
- [ ] final exact-head GitHub CI green with NumPy court;
- [ ] final generated workflow artifact inspected.

## M⁻ captured during hardening

- [x] universal `A^T A` Gram path rejected after independent NumPy baseline found false numerical null-mode inversion for wide matrices;
- [x] implementation changed to smaller Gram `A^T A` / `A A^T` according to geometry;
- [x] Gram condition-squaring limitation recorded explicitly.

## OAK boundary

- [x] low residual != unique state documented;
- [x] minimum norm != physical truth documented;
- [x] numerical rank tolerance warning documented;
- [x] regularization bias documented;
- [x] posterior prior/noise dependence documented;
- [x] local nonlinear convergence != global uniqueness documented;
- [x] stdlib Jacobi/Gram backend not presented as production SVD documented.

## Promotion rule

Keep status at `X/D candidate` until the final exact-head dedicated CI including the NumPy court passes. Promote to local `D` only for the bounded deterministic capabilities actually exercised by the tests. Do not claim broad numerical robustness or performance until scaling, tolerance and production-library campaigns are added.
