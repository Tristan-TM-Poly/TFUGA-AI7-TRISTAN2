#!/usr/bin/env python3
"""Omega-LIN-T OAKBench v0.1.

Stdlib-only local linearization benchmark for small nonlinear systems.

OAK boundary: research and education prototype only. It estimates local tangent
models, residuals, validity radius, stability, controllability, invariant loss,
and M-minus warnings. It is not a global nonlinear solver and not a control
certification tool.
"""

from __future__ import annotations

import argparse
import json
import math
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Callable, Iterable, Sequence

Vector = list[float]
Matrix = list[list[float]]
RHS = Callable[[Vector, Vector], Vector]


@dataclass(frozen=True)
class ResidualBundle:
    state_residual: float
    scaled_state_residual: float
    residual_order_estimate: str
    curvature_index: float
    max_directional_residual: float
    warnings: list[str]


@dataclass(frozen=True)
class LinearizationReport:
    system_id: str
    model: str
    x0: Vector
    u0: Vector
    f0: Vector
    A: Matrix
    B: Matrix
    c: Vector
    affine_form: str
    residuals: ResidualBundle
    residual_threshold: float
    scaled_residual_threshold: float
    valid_radius: float
    directional_validity: list[dict]
    stable_local_2d: bool | None
    controllable_2d: bool | None
    invariant_audit: dict
    oak_level: str
    oak_warnings: list[str]
    m_minus: list[str]


def vec_add(a: Sequence[float], b: Sequence[float]) -> Vector:
    return [x + y for x, y in zip(a, b)]


def vec_sub(a: Sequence[float], b: Sequence[float]) -> Vector:
    return [x - y for x, y in zip(a, b)]


def vec_scale(a: Sequence[float], s: float) -> Vector:
    return [s * x for x in a]


def mat_vec_mul(m: Matrix, v: Sequence[float]) -> Vector:
    return [sum(row[j] * v[j] for j in range(len(v))) for row in m]


def norm2(v: Sequence[float]) -> float:
    return math.sqrt(sum(x * x for x in v))


def scaled_norm(v: Sequence[float], scales: Sequence[float]) -> float:
    if len(scales) != len(v):
        raise ValueError("state_scales must match state dimension")
    total = 0.0
    for value, scale in zip(v, scales):
        if scale <= 0:
            raise ValueError("state_scales must be positive")
        total += (value / scale) ** 2
    return math.sqrt(total)


def finite_difference_jacobian_x(f: RHS, x0: Vector, u0: Vector, eps: float) -> Matrix:
    base_dim = len(f(list(x0), list(u0)))
    jac = [[0.0 for _ in x0] for _ in range(base_dim)]
    for j in range(len(x0)):
        xp = list(x0)
        xm = list(x0)
        xp[j] += eps
        xm[j] -= eps
        fp = f(xp, list(u0))
        fm = f(xm, list(u0))
        for i in range(base_dim):
            jac[i][j] = (fp[i] - fm[i]) / (2.0 * eps)
    return jac


def finite_difference_jacobian_u(f: RHS, x0: Vector, u0: Vector, eps: float) -> Matrix:
    base_dim = len(f(list(x0), list(u0)))
    jac = [[0.0 for _ in u0] for _ in range(base_dim)]
    for j in range(len(u0)):
        up = list(u0)
        um = list(u0)
        up[j] += eps
        um[j] -= eps
        fp = f(list(x0), up)
        fm = f(list(x0), um)
        for i in range(base_dim):
            jac[i][j] = (fp[i] - fm[i]) / (2.0 * eps)
    return jac


def affine_offset(f0: Vector, A: Matrix, B: Matrix, x0: Vector, u0: Vector) -> Vector:
    return vec_sub(f0, vec_add(mat_vec_mul(A, x0), mat_vec_mul(B, u0)))


def affine_prediction(A: Matrix, B: Matrix, c: Vector, x: Vector, u: Vector) -> Vector:
    return vec_add(vec_add(mat_vec_mul(A, x), mat_vec_mul(B, u)), c)


def pendulum_rhs(params: dict) -> RHS:
    g = float(params.get("g", 9.81))
    length = float(params.get("length", 1.0))
    damping = float(params.get("damping", 0.05))

    def f(x: Vector, u: Vector) -> Vector:
        theta, omega = x
        torque = u[0] if u else 0.0
        return [omega, -(g / length) * math.sin(theta) - damping * omega + torque]

    return f


def vanderpol_rhs(params: dict) -> RHS:
    mu = float(params.get("mu", 2.0))

    def f(x: Vector, u: Vector) -> Vector:
        position, velocity = x
        forcing = u[0] if u else 0.0
        return [velocity, mu * (1.0 - position * position) * velocity - position + forcing]

    return f


def duffing_rhs(params: dict) -> RHS:
    delta = float(params.get("delta", 0.2))
    alpha = float(params.get("alpha", -1.0))
    beta = float(params.get("beta", 1.0))

    def f(x: Vector, u: Vector) -> Vector:
        position, velocity = x
        forcing = u[0] if u else 0.0
        return [velocity, -delta * velocity - alpha * position - beta * position**3 + forcing]

    return f


def rhs_factory(model: str, params: dict) -> RHS:
    if model == "pendulum":
        return pendulum_rhs(params)
    if model == "vanderpol":
        return vanderpol_rhs(params)
    if model == "duffing":
        return duffing_rhs(params)
    raise ValueError(f"Unsupported model: {model}")


def default_config(system: str) -> dict:
    if system == "pendulum":
        return {
            "system_id": "omega_lin_pendulum_v0_1",
            "model": "pendulum",
            "parameters": {"g": 9.81, "length": 1.0, "damping": 0.05},
            "linearization": {"x0": [0.0, 0.0], "u0": [0.0], "state_scales": [1.0, 10.0], "max_radius": 1.2},
        }
    if system == "vanderpol":
        return {
            "system_id": "omega_lin_vanderpol_v0_1",
            "model": "vanderpol",
            "parameters": {"mu": 2.0},
            "linearization": {"x0": [1.0, 0.5], "u0": [0.0], "state_scales": [2.0, 2.0], "max_radius": 0.8, "radius_steps": 16},
        }
    if system == "duffing":
        return {
            "system_id": "omega_lin_duffing_v0_1",
            "model": "duffing",
            "parameters": {"delta": 0.2, "alpha": -1.0, "beta": 1.0},
            "linearization": {"x0": [0.0, 0.0], "u0": [0.0], "state_scales": [2.0, 2.0], "max_radius": 0.8, "radius_steps": 16},
        }
    raise ValueError(f"Unsupported --system: {system}")


def directions_2d(count: int) -> Iterable[Vector]:
    for k in range(max(4, count)):
        angle = 2.0 * math.pi * k / max(4, count)
        yield [math.cos(angle), math.sin(angle)]


def residual_for_point(f: RHS, A: Matrix, B: Matrix, c: Vector, x: Vector, u: Vector) -> Vector:
    return vec_sub(f(list(x), list(u)), affine_prediction(A, B, c, x, u))


def estimate_directional_validity(
    f: RHS,
    A: Matrix,
    B: Matrix,
    c: Vector,
    x0: Vector,
    u0: Vector,
    scales: Vector,
    threshold: float,
    scaled_threshold: float,
    max_radius: float,
    radius_steps: int,
    direction_count: int,
) -> tuple[float, float, float, list[dict]]:
    if len(x0) != 2:
        res = residual_for_point(f, A, B, c, x0, u0)
        return 0.0, norm2(res), scaled_norm(res, scales), []
    rows: list[dict] = []
    max_raw = 0.0
    max_scaled = 0.0
    for direction in directions_2d(direction_count):
        valid_radius = 0.0
        last_raw = 0.0
        last_scaled = 0.0
        for step in range(1, radius_steps + 1):
            radius = max_radius * step / radius_steps
            x = [x0[0] + radius * direction[0], x0[1] + radius * direction[1]]
            residual = residual_for_point(f, A, B, c, x, u0)
            last_raw = norm2(residual)
            last_scaled = scaled_norm(residual, scales)
            max_raw = max(max_raw, last_raw)
            max_scaled = max(max_scaled, last_scaled)
            if last_raw <= threshold and last_scaled <= scaled_threshold:
                valid_radius = radius
            else:
                break
        rows.append({"direction": [round(direction[0], 6), round(direction[1], 6)], "valid_radius": valid_radius, "last_raw_residual": last_raw, "last_scaled_residual": last_scaled})
    return min(row["valid_radius"] for row in rows), max_raw, max_scaled, rows


def hessian_curvature_index(f: RHS, x0: Vector, u0: Vector, eps: float) -> float:
    n = len(x0)
    m = len(f(list(x0), list(u0)))
    accum = 0.0
    for i in range(n):
        for j in range(n):
            xpp = list(x0); xpm = list(x0); xmp = list(x0); xmm = list(x0)
            xpp[i] += eps; xpp[j] += eps
            xpm[i] += eps; xpm[j] -= eps
            xmp[i] -= eps; xmp[j] += eps
            xmm[i] -= eps; xmm[j] -= eps
            fpp = f(xpp, list(u0)); fpm = f(xpm, list(u0)); fmp = f(xmp, list(u0)); fmm = f(xmm, list(u0))
            for k in range(m):
                second = (fpp[k] - fpm[k] - fmp[k] + fmm[k]) / (4.0 * eps * eps)
                accum += second * second
    return math.sqrt(accum)


def residual_order_estimate(f: RHS, A: Matrix, B: Matrix, c: Vector, x0: Vector, u0: Vector, r_small: float, r_large: float) -> str:
    direction = [1.0] + [0.0 for _ in x0[1:]]
    e_small = norm2(residual_for_point(f, A, B, c, vec_add(x0, vec_scale(direction, r_small)), u0))
    e_large = norm2(residual_for_point(f, A, B, c, vec_add(x0, vec_scale(direction, r_large)), u0))
    if e_small <= 1e-15 or e_large <= 1e-15:
        return "near_zero"
    order = math.log(e_large / e_small) / math.log(r_large / r_small)
    if 1.5 <= order <= 2.5:
        return f"O(radius^2)-like ({order:.3f})"
    return f"nonquadratic_or_numerical ({order:.3f})"


def eigenvalues_2x2(A: Matrix) -> tuple[complex, complex] | None:
    if len(A) != 2 or len(A[0]) != 2 or len(A[1]) != 2:
        return None
    a, b = A[0]
    c, d = A[1]
    trace = a + d
    det = a * d - b * c
    disc = trace * trace - 4.0 * det
    if disc >= 0:
        root = math.sqrt(disc)
        return ((trace + root) / 2.0 + 0j, (trace - root) / 2.0 + 0j)
    root = math.sqrt(-disc)
    return (complex(trace / 2.0, root / 2.0), complex(trace / 2.0, -root / 2.0))


def stable_continuous_2d(A: Matrix) -> bool | None:
    eig = eigenvalues_2x2(A)
    return None if eig is None else all(value.real < 0.0 for value in eig)


def controllable_2d(A: Matrix, B: Matrix, tol: float = 1e-9) -> bool | None:
    if len(A) != 2 or len(B) != 2 or not B or len(B[0]) != 1 or len(B[1]) != 1:
        return None
    b0 = [B[0][0], B[1][0]]
    ab = mat_vec_mul(A, b0)
    return abs(b0[0] * ab[1] - ab[0] * b0[1]) > tol


def invariant_audit_for_model(model: str, valid_radius: float, curvature: float) -> dict:
    base = {"valid_radius_note": f"estimated minimum directional radius {valid_radius:.6g}", "curvature_index": curvature}
    if model == "pendulum":
        base.update({"conserved": ["local phase-space tangent structure"], "lost_or_approximated": ["global periodicity", "large-angle nonlinear sine geometry", "full nonlinear energy expression"], "warnings": ["Small-angle linearization is local, not global."]})
    elif model == "vanderpol":
        base.update({"conserved": ["local tangent dynamics"], "lost_or_approximated": ["limit-cycle global geometry", "amplitude-dependent damping", "nonlinear energy injection/dissipation balance"], "warnings": ["Local linearization may miss the global attracting limit cycle."]})
    elif model == "duffing":
        base.update({"conserved": ["local tangent stiffness"], "lost_or_approximated": ["cubic stiffness far from x0", "multi-well global geometry when alpha<0", "large-amplitude nonlinear resonance"], "warnings": ["Use a multi-cell atlas before extrapolating across wells."]})
    return base


def oak_level(valid_radius: float, residuals: ResidualBundle, stable: bool | None, controllable: bool | None) -> str:
    if valid_radius <= 0:
        return "L1_local_linearization_only"
    level = "L3_residual_and_validity_domain_estimated" if residuals.scaled_state_residual > 0 else "L2_residual_measured"
    if stable is not None and controllable is not None and residuals.curvature_index >= 0:
        return "L4_dynamics_and_curvature_audited"
    return level


def run_oakbench(config: dict) -> LinearizationReport:
    model = config.get("model", "pendulum")
    lin_cfg = config.get("linearization", {})
    x0 = [float(x) for x in lin_cfg.get("x0", [0.0, 0.0])]
    u0 = [float(u) for u in lin_cfg.get("u0", [0.0])]
    eps = float(lin_cfg.get("finite_difference_epsilon", 1e-6))
    hessian_eps = float(lin_cfg.get("hessian_epsilon", max(1e-4, math.sqrt(eps))))
    threshold = float(lin_cfg.get("residual_threshold", 0.005))
    scaled_threshold = float(lin_cfg.get("scaled_residual_threshold", threshold))
    max_radius = float(lin_cfg.get("max_radius", 1.2))
    radius_steps = int(lin_cfg.get("radius_steps", 24))
    direction_count = int(lin_cfg.get("direction_count", 16))
    scales = [float(s) for s in lin_cfg.get("state_scales", [1.0 for _ in x0])]

    f = rhs_factory(model, config.get("parameters", {}))
    f0 = f(list(x0), list(u0))
    A = finite_difference_jacobian_x(f, x0, u0, eps)
    B = finite_difference_jacobian_u(f, x0, u0, eps)
    c = affine_offset(f0, A, B, x0, u0)
    valid_radius, max_raw, max_scaled, directional = estimate_directional_validity(f, A, B, c, x0, u0, scales, threshold, scaled_threshold, max_radius, radius_steps, direction_count)
    curvature = hessian_curvature_index(f, x0, u0, hessian_eps)
    order = residual_order_estimate(f, A, B, c, x0, u0, max_radius / max(radius_steps, 2), 2.0 * max_radius / max(radius_steps, 2))

    residual_warnings: list[str] = []
    if max_scaled > scaled_threshold:
        residual_warnings.append("scaled residual exceeds threshold outside certified local domain")
    if curvature > 1.0:
        residual_warnings.append("high curvature index: validity radius may shrink quickly")
    if order.startswith("nonquadratic"):
        residual_warnings.append("residual order check is not cleanly quadratic; inspect finite-difference scale")

    residuals = ResidualBundle(max_raw, max_scaled, order, curvature, max_raw, residual_warnings)
    stable = stable_continuous_2d(A)
    controllable = controllable_2d(A, B)
    warnings: list[str] = ["Research/education prototype only: no physical control certification."]
    m_minus: list[str] = []
    if any(abs(value) > 1e-10 for value in f0):
        warnings.append("x0,u0 is not an equilibrium; keep affine offset c or perturbation f0 explicitly.")
        m_minus.append("do_not_drop_affine_offset_when_not_at_equilibrium")
    if valid_radius <= 0.0:
        warnings.append("No valid radius found under chosen thresholds.")
        m_minus.append("linearization_domain_too_small")
    if valid_radius < 0.25 * max_radius:
        warnings.append("Small validity radius relative to scan radius.")
        m_minus.append("avoid_extrapolating_beyond_certified_domain")
    if stable is False:
        warnings.append("The local 2D continuous-time model is not asymptotically stable.")
    if controllable is False:
        warnings.append("The local 2D model is not controllable with supplied input channel.")

    return LinearizationReport(
        system_id=str(config.get("system_id", f"omega_lin_{model}")),
        model=model,
        x0=x0,
        u0=u0,
        f0=f0,
        A=A,
        B=B,
        c=c,
        affine_form="dx/dt ~= A x + B u + c; perturbation: d(delta_x)/dt ~= f0 + A delta_x + B delta_u",
        residuals=residuals,
        residual_threshold=threshold,
        scaled_residual_threshold=scaled_threshold,
        valid_radius=valid_radius,
        directional_validity=directional,
        stable_local_2d=stable,
        controllable_2d=controllable,
        invariant_audit=invariant_audit_for_model(model, valid_radius, curvature),
        oak_level=oak_level(valid_radius, residuals, stable, controllable),
        oak_warnings=warnings,
        m_minus=m_minus,
    )


def write_json_report(report: LinearizationReport, output_path: str | Path) -> Path:
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(asdict(report), indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return path


def markdown_report(report: LinearizationReport) -> str:
    return f"""# Omega-LIN-T report — {report.model}

Status: {report.oak_level}

## Local model

- system_id: `{report.system_id}`
- x0: `{report.x0}`
- u0: `{report.u0}`
- valid_radius: `{report.valid_radius:.6g}`
- stable_local_2d: `{report.stable_local_2d}`
- controllable_2d: `{report.controllable_2d}`

## Residuals

- raw: `{report.residuals.state_residual:.6g}`
- scaled: `{report.residuals.scaled_state_residual:.6g}`
- order: `{report.residuals.residual_order_estimate}`
- curvature: `{report.residuals.curvature_index:.6g}`

## Invariant audit

Conserved: {', '.join(report.invariant_audit.get('conserved', [])) or 'none'}

Lost or approximated: {', '.join(report.invariant_audit.get('lost_or_approximated', [])) or 'none'}

## M-minus

{chr(10).join('- ' + item for item in (report.m_minus or ['none']))}

## OAK boundary

Research/education prototype only. Not a global nonlinear solver and not a safety-critical control certification.
"""


def write_markdown_report(report: LinearizationReport, output_path: str | Path) -> Path:
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(markdown_report(report), encoding="utf-8")
    return path


def load_config(input_path: str | None, system: str) -> dict:
    if input_path:
        return json.loads(Path(input_path).read_text(encoding="utf-8"))
    return default_config(system)


def main() -> int:
    parser = argparse.ArgumentParser(description="Run Omega-LIN-T OAKBench on a supported nonlinear example.")
    parser.add_argument("--system", choices=["pendulum", "vanderpol", "duffing"], default="pendulum")
    parser.add_argument("--input", default=None, help="Optional JSON config path. Overrides --system defaults.")
    parser.add_argument("--output", required=True, help="JSON report output path.")
    parser.add_argument("--markdown-output", default=None, help="Optional Markdown report output path.")
    args = parser.parse_args()

    config = load_config(args.input, args.system)
    report = run_oakbench(config)
    write_json_report(report, args.output)
    if args.markdown_output:
        write_markdown_report(report, args.markdown_output)
    print(json.dumps(asdict(report), indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
