# Ω-INVERSE-T∞ v0.1

Status: executable scientific-computing prototype.  
Scope: local inverse construction from Taylor data, with OAK-safe branch and evidence boundaries.

## Core idea

For

\[
F(h)=f(x_0+h)-f(x_0)=\sum_{n\ge1} a_n h^n,
\qquad z=y-y_0,
\]

Ω-INVERSE-T∞ constructs a local inverse representation

\[
H(z)=\sum_{n\ge1} b_n z^n,
\qquad F(H(z))=z,
\]

and therefore

\[
f^{-1}(y)=x_0+H(y-y_0).
\]

When `a1 != 0`, this is an ordinary Taylor reversion. When the first nonzero coefficient has degree `m > 1`, the compiler switches to a Puiseux parameterization with `z=t^m` and `m` local complex branches.

## Implemented in v0.1

- exact `Fraction` arithmetic for regular formal series;
- triangular coefficient-by-coefficient reversion;
- independent formal Newton reversion
  \[
  H \leftarrow H-\frac{F(H)-z}{F'(H)};
  \]
- independent Lagrange-Bürmann coefficient oracle
  \[
  [z^n]H(z)=\frac1n[h^{n-1}]\left(\frac{h}{F(h)}\right)^n;
  \]
- deterministic three-engine agreement tests, including a 20-case rational-polynomial sweep;
- inverse derivative jet `g^(n)(y0)=n! b_n`;
- exact left/right composition checks through the requested order;
- regular / critical / degenerate invertibility gate;
- numeric complex Puiseux branches for critical truncated polynomials;
- Padé approximants;
- finite-series rational-function candidate detection;
- low-degree algebraic relation candidate detection `P(z,H(z))=0`;
- rational coefficient-ratio candidate detection;
- critical points and critical values of the supplied truncated polynomial;
- conservative OAK warnings and M-minus records;
- JSON and Markdown reports;
- no runtime dependency outside the Python standard library.

## Quick start

```bash
python scripts/omega_inverse_compiler.py --preset quadratic --order 8
python scripts/omega_inverse_compiler.py --preset exp-minus-one --order 8
python scripts/omega_inverse_compiler.py --preset lambert --order 7
python scripts/omega_inverse_compiler.py --preset sin --order 9
python scripts/omega_inverse_compiler.py --preset mobius --order 9
python scripts/omega_inverse_compiler.py --preset critical-square --order 6
python scripts/omega_inverse_lagrange.py
```

Custom local Taylor coefficients are accepted in increasing degree order:

```bash
python scripts/omega_inverse_compiler.py \
  --coefficients '0,1,1' \
  --order 8 \
  --x0 0 \
  --y0 0 \
  --output reports/omega-inverse/custom.json \
  --markdown-output reports/omega-inverse/custom.md
```

Rational coefficients can be written exactly, for example `0,1,1/2,1/6,1/24`.

## Reference examples

### `F(h)=h+h^2`

The compiler returns

\[
H(z)=z-z^2+2z^3-5z^4+14z^5-42z^6+\cdots,
\]

recognizes a finite-series algebraic candidate equivalent to

\[
z-H-H^2=0,
\]

and finds the truncated-polynomial critical point `h=-1/2`, critical value `z=-1/4`.

### `F(h)=e^h-1`

The exact reversion through supplied order matches

\[
H(z)=\log(1+z)=z-\frac{z^2}{2}+\frac{z^3}{3}-\cdots.
\]

### `F(h)=h e^h`

The coefficients match the Lambert-W expansion

\[
W(z)=\sum_{n\ge1}\frac{(-n)^{n-1}}{n!}z^n.
\]

The code verifies coefficients and compositions; the name `Lambert W` is a mathematical interpretation of that validated reference case, not a generic special-function recognizer yet.

### `F(h)=h^2`

Ordinary Taylor inversion is rejected because `F'(0)=0`. The compiler reports multiplicity two and the two leading Puiseux branches `h=+t` and `h=-t` with `z=t^2`.

## Python API

```python
from scripts.omega_inverse_compiler import compile_inverse

report = compile_inverse([0, 1, 1], order=8)
assert report.validation["left_exact_through_order"]
assert report.validation["right_exact_through_order"]
```

For a third independent coefficient check:

```python
from scripts.omega_inverse_lagrange import cross_validate_three_engines

assert cross_validate_three_engines([0, 1, 1], 8)["all_equal"]
```

Low-level functions such as `revert_series`, `revert_series_newton`, `pade`, `guess_algebraic_relation`, `critical_point_analysis`, and `puiseux_branches` can also be imported directly.

## OAK boundary

The implementation distinguishes four levels that must not be conflated:

1. **formal coefficient identity** — exact equality of truncated formal-series coefficients;
2. **local analytic interpretation** — requires the hypotheses of the inverse/implicit-function theorem and a convergence domain;
3. **candidate reconstruction** — Padé, rational, algebraic, or coefficient-pattern recognition from finite data;
4. **global inverse claim** — requires separate domain, branch, singularity, and injectivity analysis.

Three exact engines agreeing on finite formal coefficients is strong implementation evidence, but it is still not a proof of global analyticity or global invertibility. A candidate relation matching finite coefficients is not by itself a proof of an analytic identity. A Padé pole is not automatically a singularity. Critical values of a truncated Taylor polynomial are only proxies for singularities of the true inverse branch.

## Tests

```bash
python -m pytest tests/test_omega_inverse_compiler.py tests/test_omega_inverse_lagrange.py -q
```

The deterministic suites cover Catalan reversion, logarithm, Lambert-W coefficients, arcsine coefficients, Möbius rational reconstruction, Padé, critical-value analysis, Puiseux branching, derivative jets, shifted metadata, degenerate inputs, CLI reports, three-engine reference agreement, and a deterministic 20-series exact-rational sweep.

## Next layer

The natural v0.2+ extensions are:

- symbolic front-end `f(x), x0 -> Taylor jet`;
- Bell/Faà di Bruno direct inverse-derivative oracle;
- fast polynomial arithmetic / faster high-order reversion;
- certified interval bounds and analytic radius certificates;
- branch continuation atlas with predictor-corrector tracking;
- multivariate inverse jets via Jacobians, Hessians and higher tensors;
- implicit-system inversion;
- D-finite/hypergeometric/special-function recognition with holdout evidence;
- formal proof export for identities discovered by the recognition layer.
