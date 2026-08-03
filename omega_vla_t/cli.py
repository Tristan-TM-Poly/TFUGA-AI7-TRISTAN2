"""Command-line interface for Ω-VLA-T∞ R0.1."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Sequence

import numpy as np

from .core import LinearOperator, VectorSpace
from .oak import audit_operator
from .vector_calculus import graph_hodge_decomposition, graph_laplacian


def benchmark_payload(seed: int = 7) -> dict[str, object]:
    rng = np.random.default_rng(seed)
    space = VectorSpace(4, name="R4")
    matrix = rng.normal(size=(4, 4))
    matrix += np.diag([4.0, 3.0, 2.0, 1.0])
    operator = LinearOperator(matrix, space, space, name="OmegaVLAFixture")
    audit = audit_operator(operator, seed=seed)

    incidence = np.array(
        [
            [-1.0, 0.0, 1.0, -1.0],
            [1.0, -1.0, 0.0, 0.0],
            [0.0, 1.0, -1.0, 0.0],
            [0.0, 0.0, 0.0, 1.0],
        ]
    )
    flow = np.array([1.0, -0.25, 0.5, 0.75])
    hodge = graph_hodge_decomposition(incidence, flow)
    laplacian = graph_laplacian(incidence)

    return {
        "system": "Ω-VLA-T∞",
        "version": "R0.1",
        "status": "SOFTWARE_RESEARCH_FIXTURE",
        "operator": {
            "name": operator.name,
            "matrix": operator.matrix.tolist(),
            "svd": operator.svd_report().to_dict(),
            "oak": audit.to_dict(),
        },
        "graph": {
            "incidence": incidence.tolist(),
            "laplacian": laplacian.tolist(),
            "hodge": hodge.to_dict(),
        },
        "claims": {
            "theorem_claimed": False,
            "scientific_validation_claimed": False,
            "physical_law_claimed": False,
        },
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="omega-vla", description="Ω-VLA-T∞ R0.1 research-software CLI")
    subparsers = parser.add_subparsers(dest="command", required=True)

    benchmark = subparsers.add_parser("benchmark", help="run deterministic algebra and graph fixtures")
    benchmark.add_argument("--seed", type=int, default=7)
    benchmark.add_argument("--output", type=Path)

    audit = subparsers.add_parser("audit", help="audit a square matrix supplied as JSON")
    audit.add_argument("matrix", help="JSON matrix, for example '[[2,1],[0,3]]'")
    audit.add_argument("--name", default="UserOperator")
    audit.add_argument("--seed", type=int, default=0)
    audit.add_argument("--markdown", action="store_true")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)

    if args.command == "benchmark":
        payload = benchmark_payload(args.seed)
        text = json.dumps(payload, indent=2, sort_keys=True) + "\n"
        if args.output:
            args.output.parent.mkdir(parents=True, exist_ok=True)
            args.output.write_text(text, encoding="utf-8")
        else:
            print(text, end="")
        return 0

    matrix = np.asarray(json.loads(args.matrix), dtype=float)
    if matrix.ndim != 2 or matrix.shape[0] != matrix.shape[1]:
        raise SystemExit("audit requires a finite square matrix")
    space = VectorSpace(matrix.shape[0])
    operator = LinearOperator(matrix, space, space, name=args.name)
    report = audit_operator(operator, seed=args.seed)
    print(report.to_markdown() if args.markdown else json.dumps(report.to_dict(), indent=2, sort_keys=True))
    return 0 if report.passed else 2


if __name__ == "__main__":
    raise SystemExit(main())
