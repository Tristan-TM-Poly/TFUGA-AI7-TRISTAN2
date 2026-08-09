"""CLI for Ω-PURE-MATH-T∞."""

from __future__ import annotations

import argparse
import json
import operator
from typing import Sequence

from .bracket_spectrum import bracket_spectrum
from .canon import canon_summary
from .core import oak_audit_claims
from .theorem_protocol import THEOREM_CANDIDATES, protocol_as_dict


OPERATIONS = {
    "add": operator.add,
    "mul": operator.mul,
    "sub": operator.sub,
}


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="omega-pure-math",
        description="Executable formalization lab for Ω-PURE-MATH-T∞.",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    protocol = sub.add_parser("protocol", help="compile the 12-question research protocol")
    protocol.add_argument("definition")

    bracket = sub.add_parser("bracket", help="evaluate a finite bracket spectrum")
    bracket.add_argument("values", nargs="+", type=float)
    bracket.add_argument("--op", choices=sorted(OPERATIONS), default="sub")

    sub.add_parser("oak", help="audit the canonical theorem/conjecture registry")
    sub.add_parser("canon", help="emit the machine-readable branch canon")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = _parser().parse_args(argv)

    if args.command == "protocol":
        payload = protocol_as_dict(args.definition)
    elif args.command == "bracket":
        spectrum = bracket_spectrum(args.values, OPERATIONS[args.op])
        payload = {
            "operation": args.op,
            "inputs": args.values,
            "parenthesization_count": spectrum.parenthesization_count,
            "distinct_value_count": spectrum.value_count,
            "distinct_values": spectrum.distinct_values,
            "diameter": spectrum.diameter,
        }
    elif args.command == "oak":
        payload = oak_audit_claims(THEOREM_CANDIDATES).to_dict()
    else:
        payload = canon_summary()

    print(json.dumps(payload, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
