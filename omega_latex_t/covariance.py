from __future__ import annotations

import math
from typing import Any, Mapping, Sequence


class CovarianceError(ValueError):
    pass


def _matrix(value: Any) -> list[list[float]]:
    try:
        rows = [[float(x) for x in row] for row in value]
    except (TypeError, ValueError) as exc:
        raise CovarianceError("covariance must be a numeric square matrix") from exc
    n = len(rows)
    if n == 0 or any(len(row) != n for row in rows):
        raise CovarianceError("covariance must be non-empty and square")
    if any(not math.isfinite(x) for row in rows for x in row):
        raise CovarianceError("covariance entries must be finite")
    for i in range(n):
        if rows[i][i] < 0:
            raise CovarianceError("covariance diagonal must be non-negative")
        for j in range(n):
            if not math.isclose(rows[i][j], rows[j][i], rel_tol=1e-12, abs_tol=1e-15):
                raise CovarianceError("covariance matrix must be symmetric")
    _psd_cholesky(rows)
    return rows


def _psd_cholesky(rows: Sequence[Sequence[float]]) -> list[list[float]]:
    """Modified Cholesky factor for positive semidefinite matrices."""
    n = len(rows)
    scale = max(1.0, max(abs(x) for row in rows for x in row))
    tol = 1e-12 * scale
    factor = [[0.0 for _ in range(n)] for _ in range(n)]
    for i in range(n):
        for j in range(i + 1):
            residual = float(rows[i][j]) - sum(factor[i][k] * factor[j][k] for k in range(j))
            if i == j:
                if residual < -tol:
                    raise CovarianceError("covariance matrix must be positive semidefinite")
                factor[i][j] = math.sqrt(max(0.0, residual))
            elif factor[j][j] > tol:
                factor[i][j] = residual / factor[j][j]
            elif abs(residual) > tol:
                raise CovarianceError("covariance matrix must be positive semidefinite")
    return factor


def covariance_diagnostics(covariance: Any) -> dict[str, Any]:
    cov = _matrix(covariance)
    n = len(cov)
    correlations: list[dict[str, Any]] = []
    max_abs_correlation = 0.0
    for i in range(n):
        for j in range(i + 1, n):
            denom = math.sqrt(cov[i][i] * cov[j][j])
            if denom == 0:
                correlation = 0.0 if cov[i][j] == 0 else math.inf
            else:
                correlation = cov[i][j] / denom
            max_abs_correlation = max(max_abs_correlation, abs(correlation))
            correlations.append({"i": i, "j": j, "correlation": correlation})
    if max_abs_correlation > 1 + 1e-12:
        raise CovarianceError("covariance implies |correlation| > 1")
    positive_diagonal = [cov[i][i] for i in range(n) if cov[i][i] > 0]
    diagonal_ratio = max(positive_diagonal) / min(positive_diagonal) if len(positive_diagonal) >= 2 else 1.0
    return {
        "dimension": n,
        "positive_semidefinite": True,
        "max_abs_correlation": max_abs_correlation,
        "diagonal_scale_ratio": diagonal_ratio,
        "near_singular_diagonal": any(math.isclose(cov[i][i], 0.0, abs_tol=1e-15) for i in range(n)),
        "correlations": correlations,
        "boundary": "diagnostics certify algebraic covariance structure only; statistical adequacy and calibration remain external questions",
    }


def quadratic_variance(gradient: Sequence[float], covariance: Any) -> float:
    cov = _matrix(covariance)
    grad = [float(x) for x in gradient]
    if len(grad) != len(cov):
        raise CovarianceError("gradient length must match covariance dimension")
    if any(not math.isfinite(x) for x in grad):
        raise CovarianceError("gradient entries must be finite")
    value = sum(grad[i] * cov[i][j] * grad[j] for i in range(len(grad)) for j in range(len(grad)))
    if value < -1e-12:
        raise CovarianceError("quadratic variance is negative")
    return max(0.0, value)


def propagate_linear(values: Sequence[float], coefficients: Sequence[float], covariance: Any, *, unit: str = "") -> dict[str, Any]:
    vals = [float(x) for x in values]
    coeffs = [float(x) for x in coefficients]
    if len(vals) != len(coeffs):
        raise CovarianceError("values and coefficients must have equal length")
    if any(not math.isfinite(x) for x in vals + coeffs):
        raise CovarianceError("values and coefficients must be finite")
    variance = quadratic_variance(coeffs, covariance)
    return {"value": sum(a * x for a, x in zip(coeffs, vals)), "uncertainty": math.sqrt(variance), "unit": str(unit), "method": "linear-covariance", "variance": variance}


def propagate_jacobian(jacobian: Sequence[Sequence[float]], covariance: Any) -> list[list[float]]:
    cov = _matrix(covariance)
    try:
        jac = [[float(x) for x in row] for row in jacobian]
    except (TypeError, ValueError) as exc:
        raise CovarianceError("Jacobian must be a numeric matrix") from exc
    if not jac or any(len(row) != len(cov) for row in jac):
        raise CovarianceError("Jacobian column count must match covariance dimension")
    if any(not math.isfinite(x) for row in jac for x in row):
        raise CovarianceError("Jacobian entries must be finite")
    m = len(jac)
    n = len(cov)
    out = [[0.0 for _ in range(m)] for _ in range(m)]
    for a in range(m):
        for b in range(m):
            out[a][b] = sum(jac[a][i] * cov[i][j] * jac[b][j] for i in range(n) for j in range(n))
    return out


def covariance_ledger(doc: Any) -> dict[str, Any]:
    provenance = dict(getattr(doc, "provenance", {}) or {})
    models = provenance.get("covariance_models", {})
    entries = []
    if isinstance(models, Mapping):
        for model_id in sorted(models):
            raw = models[model_id]
            findings = []
            diagnostics: dict[str, Any] = {}
            try:
                if not isinstance(raw, Mapping):
                    raise CovarianceError("model must be an object")
                variables = [str(x) for x in raw.get("variables", ())]
                cov = _matrix(raw.get("covariance", ()))
                if len(variables) != len(cov):
                    raise CovarianceError("variables length must equal covariance dimension")
                units = list(raw.get("units", ()))
                if units and len(units) != len(cov):
                    raise CovarianceError("units length must be zero or equal covariance dimension")
                diagnostics = covariance_diagnostics(cov)
                normalized = {"variables": variables, "covariance": cov, "units": units, "assumptions": list(raw.get("assumptions", ()))}
            except (CovarianceError, TypeError, ValueError) as exc:
                normalized = dict(raw) if isinstance(raw, Mapping) else raw
                findings.append({"code": "COVARIANCE_MODEL_INVALID", "severity": "error", "message": str(exc)})
            entries.append({"model_id": str(model_id), "model": normalized, "diagnostics": diagnostics, "findings": findings})
    elif models not in ({}, None):
        entries.append({"model_id": "", "model": models, "diagnostics": {}, "findings": [{"code": "COVARIANCE_MODELS_INVALID", "severity": "error", "message": "covariance_models must be an object"}]})
    return {"semantic_hash": getattr(doc, "semantic_hash", lambda: "")(), "count": len(entries), "entries": entries, "boundary": "covariance algebra is first-order mathematical propagation; covariance quality, calibration, stationarity and model adequacy require external evidence"}
