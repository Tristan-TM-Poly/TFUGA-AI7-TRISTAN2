from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Sequence

from .graph import DepthGraph
from .oakgate_seed import build_oakgate_depth9
from .registry import creation_roots, find_root
from .scaffold import graph_from_root, scaffold_roots


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="omega-depth",
        description=(
            "Ω-DEPTH-T∞ recursive creation crystallizer. "
            "Finite run depths are observations/budgets, never permanent architecture ceilings."
        ),
    )
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("roots", help="List the 40 registered Tristan creation roots.")

    example = sub.add_parser(
        "oakgate-example",
        help="Generate the OAKGate example reaching observed depth n=9.",
    )
    example.add_argument("--output-dir", default="generated/omega_depth_t/oakgate-depth9")

    scaffold = sub.add_parser(
        "scaffold-all",
        help="Create depth-zero contracts and README files for all registered creations.",
    )
    scaffold.add_argument("--output-dir", default="generated/omega_depth_t/roots")

    one = sub.add_parser("scaffold-one", help="Create a finite root bundle for one creation.")
    one.add_argument("root")
    one.add_argument("--output-dir", default="generated/omega_depth_t/root")

    validate = sub.add_parser("validate", help="Validate a generated depth-graph JSON file.")
    validate.add_argument("graph")

    show = sub.add_parser("show", help="Show one node and its ancestry.")
    show.add_argument("graph")
    show.add_argument("node_id")

    children = sub.add_parser("children", help="List immediate children of one node.")
    children.add_argument("graph")
    children.add_argument("node_id")

    leaves = sub.add_parser("leaves", help="List current leaves; leaves are not permanent endpoints.")
    leaves.add_argument("graph")

    return parser


def _print(payload: object) -> None:
    print(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True))


def main(argv: Sequence[str] | None = None) -> int:
    args = _parser().parse_args(argv)

    if args.command == "roots":
        _print(
            [
                {
                    "index": root.index,
                    "slug": root.slug,
                    "id": root.node_id,
                    "name": root.name,
                    "category": root.category,
                    "oak_status": root.status.value,
                }
                for root in creation_roots()
            ]
        )
        return 0

    if args.command == "oakgate-example":
        graph = build_oakgate_depth9()
        artifacts = graph.write_bundle(args.output_dir)
        _print({"summary": graph.summary(), "artifacts": artifacts})
        return 0 if not graph.validate() else 2

    if args.command == "scaffold-all":
        _print(scaffold_roots(args.output_dir))
        return 0

    if args.command == "scaffold-one":
        root = find_root(args.root)
        output = Path(args.output_dir)
        artifacts = graph_from_root(root).write_bundle(output)
        _print({"root": root.slug, "artifacts": artifacts})
        return 0

    graph = DepthGraph.read_json(args.graph)

    if args.command == "validate":
        issues = [issue.to_dict() for issue in graph.validate()]
        _print({"summary": graph.summary(), "issues": issues})
        return 0 if not issues else 2

    if args.command == "show":
        node = graph.get(args.node_id)
        _print(
            {
                "node": node.to_dict(),
                "ancestors": [item.to_dict() for item in graph.ancestors(args.node_id)],
                "children": [item.to_dict() for item in graph.children(args.node_id)],
            }
        )
        return 0

    if args.command == "children":
        _print([item.to_dict() for item in graph.children(args.node_id)])
        return 0

    if args.command == "leaves":
        _print([item.to_dict() for item in graph.leaves()])
        return 0

    raise AssertionError(f"unsupported command: {args.command}")


if __name__ == "__main__":
    raise SystemExit(main())
