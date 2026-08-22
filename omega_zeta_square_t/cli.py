"""CLI for Ω-ZETA-SQUARE-T∞ research diagnostics and exact finite transforms."""

from __future__ import annotations

import argparse
import json
from dataclasses import asdict, is_dataclass
from fractions import Fraction
from pathlib import Path

from .bibliography import validate_bibliography_ledger
from .certificates import exact_stieltjes_certificate
from .core import nontrivial_zero_image, rh_defect
from .cvcd import cvcd_support_report
from .jacobi import jacobi_characteristic_polynomial, jacobi_recurrence_from_inverse_moments
from .materialize import materialize_from_files
from .moments import finite_stieltjes_report
from .obligations import export_obligation_bundle, obligations_from_proof_graph
from .pade import stieltjes_pade_from_inverse_moments
from .symbolic_hankel import tensor_lift_constraint


DEFAULT_GRAPH = "specs/omega_zeta_square_t/proof_graph.json"
DEFAULT_BIBLIOGRAPHY = "specs/omega_zeta_square_t/bibliography_ledger.json"


def _fraction(text: str) -> Fraction:
    try:
        return Fraction(text)
    except (ValueError, ZeroDivisionError) as exc:
        raise argparse.ArgumentTypeError(f"invalid exact rational: {text}") from exc


def _jsonable(value):
    if isinstance(value, Fraction):
        return {
            "exact": str(value),
            "numerator": value.numerator,
            "denominator": value.denominator,
        }
    if is_dataclass(value):
        return _jsonable(asdict(value))
    if isinstance(value, dict):
        return {str(k): _jsonable(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [_jsonable(v) for v in value]
    return value


def _load_json(path: str):
    return json.loads(Path(path).read_text(encoding="utf-8"))


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

    exact = sub.add_parser("exact-cert", help="exact finite Hankel/Stieltjes certificate")
    exact.add_argument("inverse_moments", nargs="+", type=_fraction)
    exact.add_argument("--hankel-size", type=int, default=2)

    pade = sub.add_parser("pade", help="exact [n-1/n] Stieltjes Padé reconstruction")
    pade.add_argument("inverse_moments", nargs="+", type=_fraction)
    pade.add_argument("--order", type=int, default=2)

    jacobi = sub.add_parser("jacobi", help="exact finite Jacobi recurrence reconstruction")
    jacobi.add_argument("inverse_moments", nargs="+", type=_fraction)
    jacobi.add_argument("--size", type=int, default=2)

    tensor = sub.add_parser(
        "tensor-constraint",
        help="compile a finite R10 Hankel determinant into sparse TensorProdLift monomials",
    )
    tensor.add_argument("--size", type=int, required=True)
    tensor.add_argument("--shift", type=int, default=0)

    cvcd = sub.add_parser("cvcd", help="minimal structural dependency supports; never a proof")
    cvcd.add_argument("target")
    cvcd.add_argument("--graph", default=DEFAULT_GRAPH)

    obligations = sub.add_parser("obligations", help="export unresolved HGFM proof obligations")
    obligations.add_argument("--graph", default=DEFAULT_GRAPH)

    bibliography = sub.add_parser("bibliography-check", help="validate KNOWN_THEOREM source bindings")
    bibliography.add_argument("--graph", default=DEFAULT_GRAPH)
    bibliography.add_argument("--ledger", default=DEFAULT_BIBLIOGRAPHY)

    materialize = sub.add_parser("materialize", help="write deterministic OAK research bundle")
    materialize.add_argument("output_dir")
    materialize.add_argument("--graph", default=DEFAULT_GRAPH)
    materialize.add_argument("--ledger", default=DEFAULT_BIBLIOGRAPHY)
    materialize.add_argument("--target", default="rh")

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
    elif args.command == "moments":
        report = finite_stieltjes_report(args.gammas, hankel_size=args.hankel_size)
        payload = {
            "schema": "omega-zeta-square-oak-receipt/2",
            **asdict(report),
            "oak": {
                "promotion": "FINITE_EVIDENCE_ONLY",
                "forbidden": ["finite_to_infinite", "numeric_to_exact"],
            },
        }
    elif args.command == "exact-cert":
        cert = exact_stieltjes_certificate(
            args.inverse_moments, hankel_size=args.hankel_size
        )
        payload = {
            "schema": "omega-zeta-square-exact-certificate/1",
            "certificate": cert,
            "oak": {
                "promotion": "EXACT_FOR_SUPPLIED_FINITE_RATIONAL_DATA_ONLY",
                "forbidden": ["finite_to_infinite", "supplied_data_to_true_xi_values"],
            },
            "proves_rh": False,
        }
    elif args.command == "pade":
        approx = stieltjes_pade_from_inverse_moments(
            args.inverse_moments, order=args.order
        )
        payload = {
            "schema": "omega-zeta-square-pade/1",
            "approximant": approx,
            "proves_rh": False,
        }
    elif args.command == "jacobi":
        recurrence = jacobi_recurrence_from_inverse_moments(
            args.inverse_moments, size=args.size
        )
        payload = {
            "schema": "omega-zeta-square-jacobi/1",
            "recurrence": recurrence,
            "characteristic_polynomial": jacobi_characteristic_polynomial(recurrence),
            "oak": {
                "promotion": "FINITE_FORMAL_RECONSTRUCTION_ONLY",
                "forbidden": ["preloaded_moments_to_independent_hilbert_polya_operator"],
            },
            "proves_rh": False,
        }
    elif args.command == "tensor-constraint":
        constraint = tensor_lift_constraint(args.size, args.shift)
        payload = {
            "schema": "omega-zeta-square-tensor-constraint/1",
            "constraint": constraint,
            "oak": {
                "promotion": "EXACT_FINITE_POLYNOMIAL_OBLIGATION_ONLY",
                "all_orders_required_for_r10": True,
                "proves_rh": False,
            },
            "proves_rh": False,
        }
    elif args.command == "cvcd":
        payload = cvcd_support_report(_load_json(args.graph), args.target)
    elif args.command == "obligations":
        graph = _load_json(args.graph)
        payload = export_obligation_bundle(obligations_from_proof_graph(graph))
    elif args.command == "bibliography-check":
        graph = _load_json(args.graph)
        ledger = _load_json(args.ledger)
        errors = validate_bibliography_ledger(graph, ledger)
        payload = {
            "schema": "omega-zeta-square-bibliography-check/1",
            "promotion": "PROMOTE" if not errors else "BLOCK",
            "errors": errors,
            "proves_rh": False,
        }
    else:
        payload = materialize_from_files(
            args.graph,
            args.ledger,
            args.output_dir,
            cvcd_target=args.target,
        )
    print(json.dumps(_jsonable(payload), indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
