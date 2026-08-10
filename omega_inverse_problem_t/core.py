from __future__ import annotations

from dataclasses import dataclass, asdict
from math import sqrt
from typing import Callable, Sequence, Any

Vector = list[float]
Matrix = list[list[float]]
NonlinearMap = Callable[[Vector], Vector]


def _as_vector(v: Sequence[float]) -> Vector:
    return [float(x) for x in v]


def _as_matrix(a: Sequence[Sequence[float]]) -> Matrix:
    rows = [[float(x) for x in row] for row in a]
    if not rows or not rows[0]:
        raise ValueError("matrix must be non-empty")
    width = len(rows[0])
    if any(len(row) != width for row in rows):
        raise ValueError("matrix rows must have equal length")
    return rows


def shape(a: Matrix) -> tuple[int, int]:
    return len(a), len(a[0])


def transpose(a: Matrix) -> Matrix:
    m, n = shape(a)
    return [[a[i][j] for i in range(m)] for j in range(n)]


def matmul(a: Matrix, b: Matrix) -> Matrix:
    ma, na = shape(a)
    mb, nb = shape(b)
    if na != mb:
        raise ValueError("matrix dimension mismatch")
    bt = transpose(b)
    return [[sum(a[i][k] * bt[j][k] for k in range(na)) for j in range(nb)] for i in range(ma)]


def matvec(a: Matrix, x: Sequence[float]) -> Vector:
    m, n = shape(a)
    if len(x) != n:
        raise ValueError("matrix/vector dimension mismatch")
    return [sum(a[i][j] * float(x[j]) for j in range(n)) for i in range(m)]


def vec_add(a: Sequence[float], b: Sequence[float]) -> Vector:
    if len(a) != len(b):
        raise ValueError("vector dimension mismatch")
    return [float(x) + float(y) for x, y in zip(a, b)]


def vec_sub(a: Sequence[float], b: Sequence[float]) -> Vector:
    if len(a) != len(b):
        raise ValueError("vector dimension mismatch")
    return [float(x) - float(y) for x, y in zip(a, b)]


def vec_scale(a: Sequence[float], s: float) -> Vector:
    return [float(s) * float(x) for x in a]


def dot(a: Sequence[float], b: Sequence[float]) -> float:
    if len(a) != len(b):
        raise ValueError("vector dimension mismatch")
    return sum(float(x) * float(y) for x, y in zip(a, b))


def norm2(a: Sequence[float]) -> float:
    return sqrt(max(0.0, dot(a, a)))


def identity(n: int) -> Matrix:
    return [[1.0 if i == j else 0.0 for j in range(n)] for i in range(n)]


def diag(values: Sequence[float]) -> Matrix:
    vals = [float(x) for x in values]
    return [[vals[i] if i == j else 0.0 for j in range(len(vals))] for i in range(len(vals))]


def matrix_add(a: Matrix, b: Matrix) -> Matrix:
    if shape(a) != shape(b):
        raise ValueError("matrix dimension mismatch")
    return [[a[i][j] + b[i][j] for j in range(len(a[0]))] for i in range(len(a))]


def matrix_scale(a: Matrix, s: float) -> Matrix:
    return [[float(s) * x for x in row] for row in a]


def inverse_matrix(a: Matrix, tol: float = 1e-14) -> Matrix:
    a = _as_matrix(a)
    n, m = shape(a)
    if n != m:
        raise ValueError("matrix must be square")
    ident = identity(n)
    aug = [a[i][:] + ident[i] for i in range(n)]
    for col in range(n):
        pivot = max(range(col, n), key=lambda r: abs(aug[r][col]))
        if abs(aug[pivot][col]) <= tol:
            raise ValueError("matrix is singular")
        if pivot != col:
            aug[col], aug[pivot] = aug[pivot], aug[col]
        scale = aug[col][col]
        aug[col] = [v / scale for v in aug[col]]
        for r in range(n):
            if r == col:
                continue
            f = aug[r][col]
            if f != 0.0:
                aug[r] = [aug[r][c] - f * aug[col][c] for c in range(2 * n)]
    return [row[n:] for row in aug]


def solve_linear(a: Matrix, b: Sequence[float]) -> Vector:
    return matvec(inverse_matrix(a), b)


def jacobi_eigh_symmetric(a: Matrix, tol: float = 1e-13, max_sweeps: int = 200) -> tuple[Vector, Matrix]:
    a = _as_matrix(a)
    n, m = shape(a)
    if n != m:
        raise ValueError("matrix must be square")
    for i in range(n):
        for j in range(n):
            if abs(a[i][j] - a[j][i]) > 1e-10:
                raise ValueError("matrix must be symmetric")
    v = identity(n)
    if n == 1:
        return [a[0][0]], v
    for _ in range(max_sweeps):
        p, q = 0, 1
        max_off = 0.0
        for i in range(n):
            for j in range(i + 1, n):
                cur = abs(a[i][j])
                if cur > max_off:
                    max_off = cur
                    p, q = i, j
        if max_off <= tol:
            break
        app, aqq, apq = a[p][p], a[q][q], a[p][q]
        tau = (aqq - app) / (2.0 * apq)
        t = (1.0 if tau >= 0 else -1.0) / (abs(tau) + sqrt(1.0 + tau * tau))
        c = 1.0 / sqrt(1.0 + t * t)
        s = t * c
        for k in range(n):
            if k in (p, q):
                continue
            akp, akq = a[k][p], a[k][q]
            a[k][p] = a[p][k] = c * akp - s * akq
            a[k][q] = a[q][k] = s * akp + c * akq
        a[p][p] = c * c * app - 2 * s * c * apq + s * s * aqq
        a[q][q] = s * s * app + 2 * s * c * apq + c * c * aqq
        a[p][q] = a[q][p] = 0.0
        for k in range(n):
            vkp, vkq = v[k][p], v[k][q]
            v[k][p] = c * vkp - s * vkq
            v[k][q] = s * vkp + c * vkq
    evals = [a[i][i] for i in range(n)]
    order = sorted(range(n), key=lambda i: evals[i], reverse=True)
    return [evals[i] for i in order], [[v[r][i] for i in order] for r in range(n)]


def _spectral_pseudoinverse_symmetric(a: Matrix, rtol: float) -> tuple[Matrix, Vector, float]:
    evals, vecs = jacobi_eigh_symmetric(a)
    singular_values = [sqrt(max(0.0, value)) for value in evals]
    largest = singular_values[0] if singular_values else 0.0
    # Forming a Gram matrix squares the condition number. The sqrt(machine-eps)
    # floor prevents inversion of numerical null modes that the Gram representation
    # cannot reliably distinguish from zero.
    threshold = max(1e-14, rtol * largest, sqrt(2.220446049250313e-16) * largest)
    inv_eigs = [
        1.0 / value if value > 0.0 and sqrt(max(0.0, value)) > threshold else 0.0
        for value in evals
    ]
    return matmul(matmul(vecs, diag(inv_eigs)), transpose(vecs)), singular_values, threshold


def singular_spectrum(a: Matrix, rtol: float = 1e-10) -> dict[str, Any]:
    a = _as_matrix(a)
    m, n = shape(a)
    # Use the smaller Gram matrix. Besides reducing work, this avoids creating
    # structural zero modes solely because a rectangular map is wide/tall.
    gram = matmul(transpose(a), a) if m >= n else matmul(a, transpose(a))
    _, singular_values, threshold = _spectral_pseudoinverse_symmetric(gram, rtol)
    rank = sum(s > threshold for s in singular_values)
    positive = [s for s in singular_values if s > threshold]
    largest = singular_values[0] if singular_values else 0.0
    smallest = min(positive) if positive else 0.0
    condition = (largest / smallest) if smallest > 0 else float("inf")
    return {
        "rows": m,
        "cols": n,
        "rank": rank,
        "nullity": n - rank,
        "left_nullity": m - rank,
        "singular_values": singular_values,
        "threshold": threshold,
        "condition_number_nonzero_subspace": condition,
        "full_column_rank": rank == n,
        "full_row_rank": rank == m,
    }


def pseudoinverse(a: Matrix, rtol: float = 1e-10) -> Matrix:
    a = _as_matrix(a)
    m, n = shape(a)
    at = transpose(a)
    if m >= n:
        gram = matmul(at, a)
        gram_plus, _, _ = _spectral_pseudoinverse_symmetric(gram, rtol)
        return matmul(gram_plus, at)
    gram = matmul(a, at)
    gram_plus, _, _ = _spectral_pseudoinverse_symmetric(gram, rtol)
    return matmul(at, gram_plus)


def least_squares(a: Matrix, y: Sequence[float], rtol: float = 1e-10) -> Vector:
    return matvec(pseudoinverse(a, rtol=rtol), y)


def tikhonov(a: Matrix, y: Sequence[float], lam: float, prior: Sequence[float] | None = None) -> Vector:
    if lam < 0:
        raise ValueError("lam must be >= 0")
    a = _as_matrix(a)
    m, n = shape(a)
    if len(y) != m:
        raise ValueError("observation dimension mismatch")
    p = [0.0] * n if prior is None else _as_vector(prior)
    if len(p) != n:
        raise ValueError("prior dimension mismatch")
    if lam == 0:
        return least_squares(a, y)
    at = transpose(a)
    lhs = matrix_add(matmul(at, a), matrix_scale(identity(n), lam))
    rhs = vec_add(matvec(at, y), vec_scale(p, lam))
    return solve_linear(lhs, rhs)


def finite_difference_jacobian(f: NonlinearMap, x: Sequence[float], eps: float = 1e-6) -> Matrix:
    x = _as_vector(x)
    base = _as_vector(f(x))
    m, n = len(base), len(x)
    j = [[0.0 for _ in range(n)] for _ in range(m)]
    for col in range(n):
        step = eps * max(1.0, abs(x[col]))
        xp, xm = x[:], x[:]
        xp[col] += step
        xm[col] -= step
        fp, fm = _as_vector(f(xp)), _as_vector(f(xm))
        if len(fp) != m or len(fm) != m:
            raise ValueError("nonlinear map output dimension changed")
        for row in range(m):
            j[row][col] = (fp[row] - fm[row]) / (2.0 * step)
    return j


@dataclass
class NonlinearInverseResult:
    x: Vector
    converged: bool
    iterations: int
    residual_norm: float
    step_norm: float
    method: str
    damping: float
    history: list[dict[str, float]]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def gauss_newton_inverse(
    f: NonlinearMap,
    y: Sequence[float],
    x0: Sequence[float],
    *,
    max_iter: int = 50,
    tol: float = 1e-10,
    damping: float = 1e-8,
    jac_eps: float = 1e-6,
) -> NonlinearInverseResult:
    x = _as_vector(x0)
    target = _as_vector(y)
    history: list[dict[str, float]] = []
    last_step = float("inf")
    for it in range(1, max_iter + 1):
        fx = _as_vector(f(x))
        if len(fx) != len(target):
            raise ValueError("observation dimension mismatch")
        r = vec_sub(target, fx)
        rnorm = norm2(r)
        if rnorm <= tol:
            return NonlinearInverseResult(x, True, it - 1, rnorm, 0.0, "levenberg-gauss-newton", damping, history)
        j = finite_difference_jacobian(f, x, eps=jac_eps)
        step = tikhonov(j, r, damping)
        last_step = norm2(step)
        alpha = 1.0
        accepted = False
        while alpha >= 2 ** -20:
            candidate = vec_add(x, vec_scale(step, alpha))
            cand_norm = norm2(vec_sub(target, _as_vector(f(candidate))))
            if cand_norm <= rnorm:
                x = candidate
                accepted = True
                break
            alpha *= 0.5
        history.append({"iteration": float(it), "residual_norm": rnorm, "step_norm": last_step, "alpha": alpha})
        if not accepted:
            break
        if last_step * alpha <= tol:
            final_r = norm2(vec_sub(target, _as_vector(f(x))))
            return NonlinearInverseResult(x, final_r <= max(tol, 1e-8), it, final_r, last_step * alpha, "levenberg-gauss-newton", damping, history)
    final_r = norm2(vec_sub(target, _as_vector(f(x))))
    return NonlinearInverseResult(x, final_r <= tol, len(history), final_r, last_step, "levenberg-gauss-newton", damping, history)


@dataclass
class LinearGaussianPosterior:
    mean: Vector
    covariance: Matrix
    information_matrix: Matrix
    residual: Vector

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def linear_gaussian_posterior(a: Matrix, y: Sequence[float], prior_mean: Sequence[float], prior_cov: Matrix, noise_cov: Matrix) -> LinearGaussianPosterior:
    a = _as_matrix(a)
    m, n = shape(a)
    yv, mu0 = _as_vector(y), _as_vector(prior_mean)
    if len(yv) != m or len(mu0) != n:
        raise ValueError("dimension mismatch")
    c0_inv = inverse_matrix(prior_cov)
    r_inv = inverse_matrix(noise_cov)
    at = transpose(a)
    info = matrix_add(c0_inv, matmul(matmul(at, r_inv), a))
    cov = inverse_matrix(info)
    rhs = vec_add(matvec(c0_inv, mu0), matvec(matmul(at, r_inv), yv))
    mean = matvec(cov, rhs)
    return LinearGaussianPosterior(mean, cov, info, vec_sub(yv, matvec(a, mean)))


def cycle_consistency_linear(a: Matrix, x: Sequence[float], *, rtol: float = 1e-10) -> dict[str, Any]:
    a = _as_matrix(a)
    xv = _as_vector(x)
    y = matvec(a, xv)
    x_hat = least_squares(a, y, rtol=rtol)
    y_hat = matvec(a, x_hat)
    return {
        "x": xv,
        "y": y,
        "x_reconstructed": x_hat,
        "y_reconstructed": y_hat,
        "inverse_residual_norm": norm2(vec_sub(x_hat, xv)),
        "forward_residual_norm": norm2(vec_sub(y_hat, y)),
        "spectrum": singular_spectrum(a, rtol=rtol),
    }


def route_linear_inverse(a: Matrix, *, noise_level: float = 0.0, regularization: float = 0.0, rtol: float = 1e-10) -> dict[str, Any]:
    spec = singular_spectrum(a, rtol=rtol)
    m, n, rank = spec["rows"], spec["cols"], spec["rank"]
    if regularization > 0 or noise_level > 0:
        method = "tikhonov"
        reason = "noise/regularization requested; prefer stabilized inverse"
    elif rank < min(m, n):
        method = "moore-penrose"
        reason = "rank deficient; return minimum-norm least-squares representative and null-space warning"
    elif m == n:
        method = "direct-or-moore-penrose"
        reason = "square full-rank map"
    elif m > n:
        method = "least-squares-moore-penrose"
        reason = "overdetermined full-column-rank map"
    else:
        method = "minimum-norm-moore-penrose"
        reason = "underdetermined full-row-rank map"
    return {"method": method, "reason": reason, "spectrum": spec}


def inverse_problem_report(a: Matrix, y: Sequence[float], *, regularization: float = 0.0, prior: Sequence[float] | None = None, rtol: float = 1e-10) -> dict[str, Any]:
    a = _as_matrix(a)
    yv = _as_vector(y)
    route = route_linear_inverse(a, regularization=regularization, rtol=rtol)
    if regularization > 0:
        x = tikhonov(a, yv, regularization, prior=prior)
        solver = "tikhonov"
    else:
        x = least_squares(a, yv, rtol=rtol)
        solver = "moore-penrose"
    yhat = matvec(a, x)
    residual = vec_sub(yhat, yv)
    warnings: list[str] = []
    spec = route["spectrum"]
    if spec["rank"] < min(spec["rows"], spec["cols"]):
        warnings.append("rank-deficient map: inverse is not unique on the full state space")
    if spec["nullity"] > 0:
        warnings.append("nontrivial null space: unobservable design/state directions exist")
    if spec["condition_number_nonzero_subspace"] > 1e5:
        warnings.append("ill-conditioned nonzero subspace: measurement noise may be strongly amplified")
    if regularization > 0:
        warnings.append("regularized solution trades exact data fit against prior/solution norm")
    return {
        "route": route,
        "solver": solver,
        "solution": x,
        "prediction": yhat,
        "residual": residual,
        "residual_norm": norm2(residual),
        "warnings": warnings,
        "oak_boundary": [
            "a numerical inverse representative is not proof of global identifiability",
            "minimum-norm selection is a convention when multiple exact preimages exist",
            "regularization encodes an assumption and can bias the reconstruction",
            "Gram-based spectral resolution is bounded by finite-precision conditioning",
        ],
    }
