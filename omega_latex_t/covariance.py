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
    return rows


def quadratic_variance(gradient: Sequence[float], covariance: Any) -> float:
    cov = _matrix(covariance); grad = [float(x) for x in gradient]
    if len(grad) != len(cov):
        raise CovarianceError("gradient length must match covariance dimension")
    value = sum(grad[i] * cov[i][j] * grad[j] for i in range(len(grad)) for j in range(len(grad)))
    if value < -1e-12:
        raise CovarianceError("quadratic variance is negative; covariance is not positive semidefinite for this gradient")
    return max(0.0, value)


def propagate_linear(values: Sequence[float], coefficients: Sequence[float], covariance: Any, *, unit: str = "") -> dict[str, Any]:
    vals = [float(x) for x in values]; coeffs = [float(x) for x in coefficients]
    if len(vals) != len(coeffs):
        raise CovarianceError("values and coefficients must have equal length")
    variance = quadratic_variance(coeffs, covariance)
    return {"value": sum(a*x for a, x in zip(coeffs, vals)), "uncertainty": math.sqrt(variance), "unit": str(unit), "method": "linear-covariance", "variance": variance}


def propagate_jacobian(jacobian: Sequence[Sequence[float]], covariance: Any) -> list[list[float]]:
    cov = _matrix(covariance)
    jac = [[float(x) for x in row] for row in jacobian]
    if not jac or any(len(row) != len(cov) for row in jac):
        raise CovarianceError("Jacobian column count must match covariance dimension")
    m = len(jac); n = len(cov)
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
            try:
                if not isinstance(raw, Mapping): raise CovarianceError("model must be an object")
                variables = [str(x) for x in raw.get("variables", ())]
                cov = _matrix(raw.get("covariance", ()))
                if len(variables) != len(cov): raise CovarianceError("variables length must equal covariance dimension")
                normalized = {"variables": variables, "covariance": cov, "units": list(raw.get("units", ())), "assumptions": list(raw.get("assumptions", ())) }
            except CovarianceError as exc:
                normalized = dict(raw) if isinstance(raw, Mapping) else raw
                findings.append({"code": "COVARIANCE_MODEL_INVALID", "severity": "error", "message": str(exc)})
            entries.append({"model_id": str(model_id), "model": normalized, "findings": findings})
    return {"semantic_hash": getattr(doc, "semantic_hash", lambda: "")(), "count": len(entries), "entries": entries, "boundary": "covariance algebra is first-order mathematical propagation; covariance quality, calibration, stationarity and model adequacy require external evidence"}
