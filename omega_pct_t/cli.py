from __future__ import annotations

from argparse import ArgumentParser
from pathlib import Path
import json

from .core import ModelRegistry
from .frontier import AdaptiveFrontier, FrontierBudget, synthetic_particle_candidates
from .hypercomplex import audit_basis
from .pipeline import OmegaPCTPipeline


def build_parser() -> ArgumentParser:
    parser = ArgumentParser(prog="omega-pct", description="Ω-PARTICULES-CHAMPS-T∞ OAK-safe research kernel")
    sub = parser.add_subparsers(dest="command", required=True)

    catalog = sub.add_parser("catalog", help="Validate and summarize a particle-field catalog")
    catalog.add_argument("catalog")
    catalog.add_argument("--json", action="store_true")

    qed = sub.add_parser("qed-reference", help="Run the e-mu two-body reference pipeline")
    qed.add_argument("catalog")
    qed.add_argument("--output-dir", default="generated/omega_pct_t/qed-reference")
    qed.add_argument("--count", type=int, default=256)
    qed.add_argument("--sqrt-s", type=float, default=10.0)
    qed.add_argument("--seed", type=int, default=0)

    hyper = sub.add_parser("hypercomplex-audit", help="Audit Cayley-Dickson representation hazards")
    hyper.add_argument("--dimension", type=int, default=16)
    hyper.add_argument("--skip-zero-divisors", action="store_true")

    frontier = sub.add_parser("frontier", help="Run a resource-bounded stream without a fixed item ceiling")
    frontier.add_argument("--output", default="generated/omega_pct_t/frontier/candidates.jsonl")
    frontier.add_argument("--checkpoint")
    frontier.add_argument("--max-seconds", type=float, default=1.0)
    frontier.add_argument("--max-bytes", type=int)
    frontier.add_argument("--max-failures", type=int, default=100)
    frontier.add_argument("--initial-batch", type=int, default=256)
    frontier.add_argument("--max-batch-by-resource", type=int)
    frontier.add_argument("--namespaces", type=int, default=16)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.command == "catalog":
        registry = ModelRegistry.from_catalog(args.catalog)
        issues = registry.validate()
        summary = {
            "fields": len(registry.fields), "particles": len(registry.particles), "interactions": len(registry.interactions),
            "errors": sum(issue.severity == "error" for issue in issues), "warnings": sum(issue.severity == "warning" for issue in issues),
            "issues": [issue.__dict__ for issue in issues],
        }
        print(json.dumps(summary, indent=2, ensure_ascii=False, sort_keys=True) if args.json else summary)
        return 1 if summary["errors"] else 0
    if args.command == "qed-reference":
        report = OmegaPCTPipeline.from_catalog(args.catalog).run_qed_reference(args.output_dir, count=args.count, sqrt_s=args.sqrt_s, seed=args.seed)
        print(json.dumps(report.to_dict(), indent=2, ensure_ascii=False, sort_keys=True))
        return 0 if report.combined_report["passed"] else 1
    if args.command == "hypercomplex-audit":
        report = audit_basis(args.dimension, not args.skip_zero_divisors)
        print(json.dumps(report.__dict__, indent=2, ensure_ascii=False, sort_keys=True))
        return 0
    if args.command == "frontier":
        budget = FrontierBudget(
            max_seconds=args.max_seconds, max_bytes=args.max_bytes, max_failures=args.max_failures,
            initial_batch=args.initial_batch, max_batch_by_resource=args.max_batch_by_resource,
        )
        engine = AdaptiveFrontier(budget)
        def validate(item):
            required = {"id", "status", "provenance", "falsifier"}
            missing = sorted(required - item.keys())
            return (not missing, 1.0 if not missing else 0.0, "ok" if not missing else f"missing:{','.join(missing)}")
        state = engine.run(synthetic_particle_candidates(args.namespaces), args.output, validate, lambda item: str(item["id"]), args.checkpoint)
        print(json.dumps(state.__dict__, indent=2, ensure_ascii=False, sort_keys=True))
        return 0
    return 2
