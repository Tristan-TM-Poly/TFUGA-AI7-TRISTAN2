from __future__ import annotations

import argparse
import json
from pathlib import Path

from .core import (
    gauss_newton_inverse,
    inverse_problem_report,
    linear_gaussian_posterior,
    matvec,
)


def preset(name: str) -> dict:
    if name == "sensor-overdetermined":
        a = [[1.0, 0.0], [0.0, 1.0], [1.0, 1.0]]
        x_true = [2.0, -1.0]
        return {"kind": "linear", "A": a, "y": matvec(a, x_true), "x_true": x_true, "regularization": 0.0}
    if name == "design-underdetermined":
        return {"kind": "linear", "A": [[1.0, 1.0]], "y": [2.0], "regularization": 0.0}
    if name == "ill-conditioned":
        return {"kind": "linear", "A": [[1.0, 0.0], [0.0, 1e-9]], "y": [1.0, 1e-9], "regularization": 1e-6}
    if name == "bayes-scalar":
        return {
            "kind": "bayes",
            "A": [[1.0]],
            "y": [2.0],
            "prior_mean": [0.0],
            "prior_cov": [[1.0]],
            "noise_cov": [[1.0]],
        }
    if name == "nonlinear-calibration":
        return {"kind": "nonlinear", "y": [1.14, 0.6], "x0": [1.0, 0.0]}
    raise ValueError(f"unknown preset: {name}")


def run_preset(name: str) -> dict:
    cfg = preset(name)
    if cfg["kind"] == "linear":
        report = inverse_problem_report(
            cfg["A"],
            cfg["y"],
            regularization=cfg.get("regularization", 0.0),
        )
        report["preset"] = name
        if "x_true" in cfg:
            report["x_true"] = cfg["x_true"]
        return report
    if cfg["kind"] == "bayes":
        posterior = linear_gaussian_posterior(
            cfg["A"], cfg["y"], cfg["prior_mean"], cfg["prior_cov"], cfg["noise_cov"]
        )
        return {
            "preset": name,
            "posterior": posterior.to_dict(),
            "oak_boundary": [
                "posterior depends on the declared prior and noise model",
                "probability mass is not proof of physical uniqueness",
            ],
        }
    if cfg["kind"] == "nonlinear":
        def f(v: list[float]) -> list[float]:
            return [v[0] ** 2 + v[1], v[0] + 2.0 * v[1]]

        result = gauss_newton_inverse(f, cfg["y"], cfg["x0"], damping=1e-8)
        return {
            "preset": name,
            "result": result.to_dict(),
            "forward_check": f(result.x),
            "oak_boundary": [
                "local nonlinear convergence depends on initialization and geometry",
                "one converged branch does not establish global uniqueness",
            ],
        }
    raise AssertionError("unreachable")


def markdown(report: dict) -> str:
    lines = ["# Ω-INVERSE-PROBLEM-T∞ report", "", f"Preset: `{report.get('preset', 'custom')}`", ""]
    if "solver" in report:
        lines += [
            f"- solver: `{report['solver']}`",
            f"- residual norm: `{report['residual_norm']:.12g}`",
            f"- solution: `{report['solution']}`",
            f"- route: `{report['route']['method']}`",
            f"- rank: `{report['route']['spectrum']['rank']}`",
            f"- nullity: `{report['route']['spectrum']['nullity']}`",
        ]
    elif "posterior" in report:
        lines += [
            f"- posterior mean: `{report['posterior']['mean']}`",
            f"- posterior covariance: `{report['posterior']['covariance']}`",
        ]
    elif "result" in report:
        lines += [
            f"- converged: `{report['result']['converged']}`",
            f"- residual norm: `{report['result']['residual_norm']:.12g}`",
            f"- solution: `{report['result']['x']}`",
        ]
    if report.get("warnings"):
        lines += ["", "## Warnings"] + [f"- {item}" for item in report["warnings"]]
    lines += ["", "## OAK boundary"] + [f"- {item}" for item in report.get("oak_boundary", [])]
    return "\n".join(lines) + "\n"


def main() -> None:
    parser = argparse.ArgumentParser(description="Ω-INVERSE-PROBLEM-T∞ reference CLI")
    parser.add_argument(
        "--preset",
        required=True,
        choices=["sensor-overdetermined", "design-underdetermined", "ill-conditioned", "bayes-scalar", "nonlinear-calibration"],
    )
    parser.add_argument("--output")
    parser.add_argument("--markdown-output")
    args = parser.parse_args()
    report = run_preset(args.preset)
    text = json.dumps(report, indent=2, sort_keys=True)
    print(text)
    if args.output:
        path = Path(args.output)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text + "\n", encoding="utf-8")
    if args.markdown_output:
        path = Path(args.markdown_output)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(markdown(report), encoding="utf-8")


if __name__ == "__main__":
    main()
