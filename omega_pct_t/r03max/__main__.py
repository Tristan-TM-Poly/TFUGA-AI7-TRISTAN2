from __future__ import annotations

from dataclasses import asdict
import argparse
import json
from pathlib import Path

from .lagrangian_ir import load_theory
from .model_generator import dark_vector_candidate, scalar_portal_candidate
from .oakbench import OAKBench
from .pdg_absorber import absorb_snapshot


def main() -> int:
    parser = argparse.ArgumentParser(prog="python -m omega_pct_t.r03max")
    subparsers = parser.add_subparsers(dest="command", required=True)

    compile_parser = subparsers.add_parser("compile")
    compile_parser.add_argument("theory")

    oak_parser = subparsers.add_parser("oak")
    oak_parser.add_argument("theory")

    candidate_parser = subparsers.add_parser("candidate")
    candidate_parser.add_argument("kind", choices=("scalar-portal", "dark-vector"))

    absorb_parser = subparsers.add_parser("absorb-pdg")
    absorb_parser.add_argument("payload")
    absorb_parser.add_argument("--edition", required=True)
    absorb_parser.add_argument("--cutoff-date", required=True)
    absorb_parser.add_argument("--source-locator", required=True)
    absorb_parser.add_argument("--output-dir", required=True)

    arguments = parser.parse_args()
    if arguments.command == "compile":
        from .lagrangian_ir import LagrangianCompiler

        result = LagrangianCompiler().compile(load_theory(arguments.theory))
        print(json.dumps(asdict(result), indent=2, sort_keys=True, default=str))
        return 0 if result.passed_structural_compilation else 2
    if arguments.command == "oak":
        result = OAKBench().evaluate(load_theory(arguments.theory))
        print(json.dumps(asdict(result), indent=2, sort_keys=True, default=str))
        return 0 if result.passed else 3
    if arguments.command == "candidate":
        candidate = (
            scalar_portal_candidate()
            if arguments.kind == "scalar-portal"
            else dark_vector_candidate()
        )
        print(json.dumps(asdict(candidate), indent=2, sort_keys=True, default=str))
        return 0
    if arguments.command == "absorb-pdg":
        payload = json.loads(Path(arguments.payload).read_text(encoding="utf-8"))
        manifest = absorb_snapshot(
            payload,
            edition=arguments.edition,
            cutoff_date=arguments.cutoff_date,
            source_locator=arguments.source_locator,
            output_directory=arguments.output_dir,
        )
        print(json.dumps(asdict(manifest), indent=2, sort_keys=True))
        return 0
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
