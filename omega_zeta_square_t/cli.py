"""CLI for Ω-ZETA-SQUARE-T∞ finite research diagnostics."""

from __future__ import annotations

import argparse
import json
from dataclasses import asdict

from .core import nontrivial_zero_image, rh_defect
from .moments import finite_stieltjes_report


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="omega-zeta-square",
        description="Centered-square RH research diagnostics; never claims an RH proof.",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    geometry = sub.add_parser("geometry", help="map beta+i gamma through u=(s-1/2)^2")
    geometry.add_argument("beta", type=float)
    geometry.add_argument("gamma", type=float)

    moments = sub.add_parser("moments", help="finite inverse-moment/Hankel OAK receipt")
    moments.add_argument("gammas", nargs="+", type=float)
    moments.add_argument("--hankel-size", type=int, default=2)

    return parser


def main(argv=None) -> int:
    args = _parser().parse_args(argv)
    if args.command == "geometry":
        u = nontrivial_zero_image(args.beta, args.gamma)
        payload = {
            "schema": "omega-zeta-square-geometry/1",
            "beta": args.beta,
            "gamma": args.gamma,
            "u": {"real": u.real, "imag": u.imag},
            "D_RH": rh_defect(u),
            "epistemic_status": "EXACT_IDENTITY_EVALUATED_NUMERICALLY",
            "proves_rh": False,
        }
    else:
        report = finite_stieltjes_report(args.gammas, hankel_size=args.hankel_size)
        payload = {
            "schema": "omega-zeta-square-oak-receipt/1",
            **asdict(report),
            "oak": {
                "promotion": "FINITE_EVIDENCE_ONLY",
                "forbidden": ["finite_to_infinite", "numeric_to_exact"],
            },
        }
    print(json.dumps(payload, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
