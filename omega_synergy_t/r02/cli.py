"""CLI for Ω-SYNERGY-OS-T∞ R0.2 MAX."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from .kernel import KernelPolicy, SynergyOSKernel, demo_inputs
from .manifest import compare_bundles, verify_bundle, write_bundle
from .portfolio import PortfolioPolicy
from .seed import top_constellations


def _load_json_records(path: Path) -> list[Any]:
    if path.suffix.lower() == ".jsonl":
        records = []
        for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
            if not line.strip():
                continue
            try:
                records.append(json.loads(line))
            except json.JSONDecodeError as exc:
                raise ValueError(f"invalid JSONL {path}:{line_number}: {exc}") from exc
        return records
    payload = json.loads(path.read_text(encoding="utf-8"))
    if isinstance(payload, list):
        return payload
    if isinstance(payload, dict):
        for key in ("records", "items", "creations", "experiments", "work_units", "proofs"):
            if isinstance(payload.get(key), list):
                return list(payload[key])
        return [payload]
    raise ValueError(f"input {path} must contain an object or array")


def _parse_input(specification: str) -> tuple[str, Path]:
    if "=" not in specification:
        raise ValueError("--input must use KIND=PATH")
    kind, path_text = specification.split("=", 1)
    kind = kind.strip().lower()
    path = Path(path_text).expanduser().resolve()
    if not kind:
        raise ValueError("input kind must not be empty")
    if not path.is_file():
        raise ValueError(f"input file does not exist: {path}")
    return kind, path


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="omega-synergy-os",
        description="Ω-SYNERGY-OS-T∞ R0.2 review-only Transformation IR and synergy portfolio compiler",
    )
    sub = parser.add_subparsers(dest="command", required=True)
    demo = sub.add_parser("demo", help="compile the deterministic cross-system demonstration")
    demo.add_argument("--output-dir", default="generated/omega_synergy_os_r02/demo")
    demo.add_argument("--budget", type=float, default=4.0)
    demo.add_argument("--max-items", type=int, default=4)
    compile_cmd = sub.add_parser("compile", help="compile typed JSON/JSONL records into a review bundle")
    compile_cmd.add_argument("--input", action="append", default=[], metavar="KIND=PATH")
    compile_cmd.add_argument("--output-dir", default="generated/omega_synergy_os_r02/compile")
    compile_cmd.add_argument("--budget", type=float, default=4.0)
    compile_cmd.add_argument("--max-items", type=int, default=4)
    compile_cmd.add_argument("--bridge-threshold", type=float, default=0.45)
    compile_cmd.add_argument("--materialize-top-bridges", type=int, default=24)
    compile_cmd.add_argument("--no-seed-constellations", action="store_true")
    compile_cmd.add_argument("--source-head", action="append", default=[], metavar="REPO=SHA")
    seed = sub.add_parser("seed", help="write the six canonical strategic constellations")
    seed.add_argument("--output", default="generated/omega_synergy_os_r02/top_constellations.json")
    audit = sub.add_parser("audit", help="verify hashes, Merkle root and authority boundaries")
    audit.add_argument("--bundle-dir", required=True)
    compare = sub.add_parser("compare", help="compare two deterministic bundle manifests")
    compare.add_argument("left")
    compare.add_argument("right")
    return parser


def _parse_heads(values: list[str]) -> dict[str, str]:
    heads: dict[str, str] = {}
    for value in values:
        if "=" not in value:
            raise ValueError("--source-head must use REPO=SHA")
        repository, sha = value.split("=", 1)
        repository = repository.strip()
        sha = sha.strip()
        if not repository or not sha:
            raise ValueError("--source-head requires non-empty repository and SHA")
        heads[repository] = sha
    return heads


def _kernel_from_args(args: argparse.Namespace) -> SynergyOSKernel:
    portfolio_policy = PortfolioPolicy(budget=args.budget, max_items=args.max_items)
    policy = KernelPolicy(
        bridge_threshold=getattr(args, "bridge_threshold", 0.45),
        materialize_top_bridges=getattr(args, "materialize_top_bridges", 24),
        include_seed_constellations=not getattr(args, "no_seed_constellations", False),
        portfolio_policy=portfolio_policy,
        source_heads=_parse_heads(getattr(args, "source_head", [])),
    )
    return SynergyOSKernel(policy)


def run(args: argparse.Namespace) -> dict[str, Any]:
    if args.command == "seed":
        output = Path(args.output)
        output.parent.mkdir(parents=True, exist_ok=True)
        payload = [item.to_dict() for item in top_constellations()]
        output.write_text(json.dumps(payload, indent=2, ensure_ascii=False, sort_keys=True) + "\n", encoding="utf-8")
        return {"output": str(output), "constellations": len(payload), "authority": "review_only_heuristic"}
    if args.command == "audit":
        return verify_bundle(args.bundle_dir)
    if args.command == "compare":
        return compare_bundles(args.left, args.right)
    if args.command == "demo":
        kernel = _kernel_from_args(args)
        result = kernel.compile(demo_inputs(), available_evidence=["PR-338", "PR-347", "PR-234", "PR-346", "PR-318", "PR-243", "PR-332", "PR-292", "PR-259"])
        written = write_bundle(result, args.output_dir)
        return {
            "output_dir": str(written.output_dir), "bundle_id": written.manifest.bundle_id,
            "ir_digest": written.manifest.ir_digest, "nodes": len(result.bundle.ir.nodes),
            "edges": len(result.bundle.ir.edges), "bridges": len(result.bridge_candidates),
            "constellations": len(result.bundle.constellations), "selected": result.bundle.portfolio.selected_ids,
            "authority": "A3", "automatic_merge_allowed": False,
        }
    if args.command == "compile":
        inputs: dict[str, list[Any]] = {}
        for specification in args.input:
            kind, path = _parse_input(specification)
            inputs.setdefault(kind, []).extend(_load_json_records(path))
        if not inputs:
            raise ValueError("compile requires at least one --input KIND=PATH")
        kernel = _kernel_from_args(args)
        result = kernel.compile(inputs)
        written = write_bundle(result, args.output_dir)
        return {
            "output_dir": str(written.output_dir), "bundle_id": written.manifest.bundle_id,
            "ir_digest": written.manifest.ir_digest, "nodes": len(result.bundle.ir.nodes),
            "edges": len(result.bundle.ir.edges), "bridges": len(result.bridge_candidates),
            "constellations": len(result.bundle.constellations), "selected": result.bundle.portfolio.selected_ids,
            "residuals": len(result.bundle.m_minus), "authority": "A3", "automatic_merge_allowed": False,
        }
    raise ValueError(f"unsupported command: {args.command}")


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        payload = run(args)
    except (ValueError, OSError, json.JSONDecodeError) as exc:
        parser.error(str(exc))
    print(json.dumps(payload, indent=2, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
