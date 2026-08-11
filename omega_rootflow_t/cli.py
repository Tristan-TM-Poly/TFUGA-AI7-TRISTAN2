"""CLI for Ω-ROOTFLOW-T∞."""

from __future__ import annotations

import argparse
import json
from fractions import Fraction
from pathlib import Path
from typing import Sequence

import numpy as np

from .adaptive import continue_roots_adaptive
from .basis import conditioning_atlas
from .collision_manifold import audit_tangent_prediction, collision_tangent_space
from .continuation import continue_roots
from .core import root_conditions, root_jacobian, roots
from .exact import audit_exact_algebra
from .invariants import audit_invariants
from .kinematics import parameter_root_kinematics, taylor_predict_roots
from .monodromy import quadratic_square_root_loop, track_coefficient_path
from .monodromy_group import generate_monodromy_group
from .multiplicity_strata import audit_multiplicity_prediction, exact_root_multiplicity, multiplicity_tangent_space
from .oak import audit_rootflow
from .projective import projective_roots
from .projective_flow import cubic_degree_collapse_path, track_projective_path
from .puiseux import canonical_puiseux_fit
from .resultant import audit_discriminant, single_coefficient_collision_atlas
from .spectral import audit_spectral_geometry, inverse_design_roots
from .spectral_hgfm import build_spectral_hgfm
from .versal import analyze_unfolding_direction, local_unfolding_map, local_unfolding_roots, real_parameter_tangent_space

VERSION = "R0.8"
LEGACY_PAYLOAD_VERSION = "R0.6"
NATIVE_MODE_VERSIONS = {
    "exact-rational-root-multiplicity": "R0.7",
    "multiplicity-tangent-stratum": "R0.7",
    "real-parameter-multiplicity-tangent": "R0.8",
    "local-versal-unfolding": "R0.8",
}


def _parse_complex_vector(text: str, *, minimum: int = 1) -> np.ndarray:
    try:
        values = [complex(part.strip()) for part in text.split(",") if part.strip()]
    except ValueError as exc:
        raise argparse.ArgumentTypeError(f"invalid complex value: {exc}") from exc
    if len(values) < minimum:
        raise argparse.ArgumentTypeError(f"provide at least {minimum} comma-separated values")
    return np.asarray(values, dtype=np.complex128)


def _parse_coefficients(text: str) -> np.ndarray:
    return _parse_complex_vector(text, minimum=2)


def _parse_roots(text: str) -> np.ndarray:
    return _parse_complex_vector(text)


def _parse_exact_coefficients(text: str) -> tuple[str, ...]:
    tokens = tuple(part.strip() for part in text.split(",") if part.strip())
    if len(tokens) < 2:
        raise argparse.ArgumentTypeError("provide at least two exact rational coefficients")
    try:
        for token in tokens:
            Fraction(token)
    except (ValueError, ZeroDivisionError) as exc:
        raise argparse.ArgumentTypeError(f"invalid exact rational coefficient: {exc}") from exc
    return tokens


def _parse_degrees(text: str) -> tuple[int, ...]:
    try:
        values = tuple(int(part.strip()) for part in text.split(",") if part.strip())
    except ValueError as exc:
        raise argparse.ArgumentTypeError(f"invalid coefficient degree: {exc}") from exc
    if not values:
        raise argparse.ArgumentTypeError("provide at least one coefficient degree")
    return values


def _complex(value: complex) -> dict[str, float]:
    return {"real": float(value.real), "imag": float(value.imag)}


def _complex_vector(values: np.ndarray) -> list[dict[str, float]]:
    return [_complex(complex(value)) for value in values]


def _base(mode: str) -> dict[str, object]:
    payload_version = NATIVE_MODE_VERSIONS.get(mode, LEGACY_PAYLOAD_VERSION)
    return {"system": "Ω-ROOTFLOW-T∞", "version": payload_version, "engine_version": VERSION, "mode": mode}


def analyze_payload(coefficients: np.ndarray) -> dict[str, object]:
    rr = roots(coefficients)
    payload = _base("analyze")
    payload.update({
        "coefficient_order": "ascending [a0,...,an]",
        "degree": int(coefficients.size - 1),
        "roots": _complex_vector(rr),
        "conditions": [{"root": _complex(item.root), "derivative_magnitude": item.derivative_magnitude, "reciprocal_derivative": item.reciprocal_derivative, "residual": item.residual, "near_singular": item.near_singular} for item in root_conditions(coefficients, rr)],
        "root_jacobian": [[_complex(complex(value)) for value in row] for row in root_jacobian(coefficients, rr)],
        "audit": audit_rootflow(coefficients).to_dict(),
        "spectral_audit": audit_spectral_geometry(coefficients).to_dict(),
        "claims": {"theorem_claimed": False, "scientific_validation_claimed": False},
    })
    return payload


def exact_audit_payload(coefficients: tuple[str, ...]) -> dict[str, object]:
    payload = _base("exact-rational-algebra-audit"); payload["audit"] = audit_exact_algebra(coefficients).to_dict(); return payload


def exact_multiplicity_payload(coefficients: tuple[str, ...], root: str) -> dict[str, object]:
    payload = _base("exact-rational-root-multiplicity"); payload.update({"root": root, "multiplicity": exact_root_multiplicity(coefficients, root), "claims": {"theorem_claimed": False, "scientific_validation_claimed": False}}); return payload


def collision_tangent_payload(coefficients: np.ndarray, critical_root: complex, degrees: tuple[int, ...], epsilon: float) -> dict[str, object]:
    tangent = collision_tangent_space(coefficients, critical_root, degrees); payload = _base("collision-tangent-space"); payload["tangent"] = tangent.to_dict(); payload["prediction_audit"] = audit_tangent_prediction(coefficients, tangent, epsilon=epsilon).to_dict() if tangent.status.startswith("OAK_PASS") else None; return payload


def multiplicity_tangent_payload(coefficients: np.ndarray, critical_root: complex, multiplicity: int, degrees: tuple[int, ...], epsilon: float) -> dict[str, object]:
    stratum = multiplicity_tangent_space(coefficients, critical_root, multiplicity, degrees); payload = _base("multiplicity-tangent-stratum"); payload["stratum"] = stratum.to_dict(); payload["prediction_audit"] = audit_multiplicity_prediction(coefficients, stratum, epsilon=epsilon).to_dict() if stratum.status == "OAK_PASS_MULTIPLICITY_TANGENT_SPACE" else None; return payload


def real_tangent_payload(coefficients: np.ndarray, critical_root: complex, multiplicity: int, degrees: tuple[int, ...]) -> dict[str, object]:
    real = real_parameter_tangent_space(coefficients, critical_root, multiplicity, degrees)
    payload = _base("real-parameter-multiplicity-tangent")
    payload["real_tangent"] = real.to_dict()
    payload["claims"] = {"theorem_claimed": False, "scientific_validation_claimed": False, "scope": "realification of local complex multiplicity constraints"}
    return payload


def unfolding_payload(coefficients: np.ndarray, critical_root: complex, multiplicity: int, degrees: tuple[int, ...], direction: np.ndarray, epsilon: float) -> dict[str, object]:
    unfolding = local_unfolding_map(coefficients, critical_root, multiplicity, degrees)
    analysis = analyze_unfolding_direction(unfolding, direction)
    local_roots = local_unfolding_roots(unfolding, direction, epsilon)
    payload = _base("local-versal-unfolding")
    payload.update({
        "unfolding": unfolding.to_dict(),
        "direction_analysis": analysis.to_dict(),
        "epsilon": float(epsilon),
        "local_model_roots": _complex_vector(local_roots),
        "claims": {"theorem_claimed": False, "scientific_validation_claimed": False, "scope": "translation-normalized first-order local unfolding and truncated-model roots"},
    })
    return payload


def invariant_payload(coefficients: np.ndarray) -> dict[str, object]:
    payload = _base("vieta-newton-residue-invariants"); payload["audit"] = audit_invariants(coefficients).to_dict(); return payload


def discriminant_payload(coefficients: np.ndarray) -> dict[str, object]:
    payload = _base("resultant-discriminant-crosscheck"); payload["audit"] = audit_discriminant(coefficients).to_dict(); return payload


def collisions_payload(coefficients: np.ndarray, coefficient_degree: int) -> dict[str, object]:
    payload = _base("single-coefficient-collision-atlas"); payload["atlas"] = single_coefficient_collision_atlas(coefficients, coefficient_degree).to_dict(); return payload


def kinematics_payload(coefficients: np.ndarray, velocity: np.ndarray, acceleration: np.ndarray | None, delta: complex) -> dict[str, object]:
    state = parameter_root_kinematics(coefficients, velocity, acceleration); payload = _base("parameter-root-kinematics"); payload.update({"kinematics": state.to_dict(), "delta_parameter": _complex(delta), "first_order_prediction": _complex_vector(taylor_predict_roots(state, delta, order=1)), "second_order_prediction": _complex_vector(taylor_predict_roots(state, delta, order=2)), "claims": {"theorem_claimed": False, "scientific_validation_claimed": False}}); return payload


def spectral_payload(coefficients: np.ndarray) -> dict[str, object]:
    payload = _base("spectral-crosscheck"); payload["audit"] = audit_spectral_geometry(coefficients).to_dict(); return payload


def basis_atlas_payload(coefficients: np.ndarray) -> dict[str, object]:
    payload = _base("basis-conditioning-atlas"); payload["atlas"] = conditioning_atlas(coefficients).to_dict(); return payload


def projective_payload(coefficients: np.ndarray) -> dict[str, object]:
    payload = _base("projective-spectrum"); payload["spectrum"] = projective_roots(coefficients).to_dict(); return payload


def projective_flow_demo_payload(samples: int) -> dict[str, object]:
    payload = _base("projective-degree-flow-demo"); payload["result"] = track_projective_path(cubic_degree_collapse_path(samples)).to_dict(); return payload


def puiseux_demo_payload(multiplicity: int) -> dict[str, object]:
    payload = _base("puiseux-canonical-demo"); payload["result"] = canonical_puiseux_fit(multiplicity).to_dict(); return payload


def monodromy_demo_payload(samples: int, subdivisions: int) -> dict[str, object]:
    payload = _base("monodromy-demo-z2-minus-t"); payload["result"] = track_coefficient_path(quadratic_square_root_loop(samples), subdivisions=subdivisions).to_dict(); return payload


def monodromy_group_demo_payload() -> dict[str, object]:
    payload = _base("monodromy-group-demo"); payload["group"] = generate_monodromy_group([(1, 0)]).to_dict(); return payload


def hgfm_demo_payload(samples: int) -> dict[str, object]:
    payload = _base("spectral-hgfm-demo"); payload["graph"] = build_spectral_hgfm(cubic_degree_collapse_path(samples)).to_dict(); return payload


def continuation_payload(start: np.ndarray, end: np.ndarray, steps: int) -> dict[str, object]:
    result = continue_roots(start, end, steps=steps); payload = _base("fixed-step"); payload["steps"] = [{"t": item.parameter, "roots": _complex_vector(item.roots), "predictor_residual": item.predictor_residual, "corrected_residual": item.corrected_residual, "minimum_derivative": item.minimum_derivative} for item in result.steps]; return payload


def adaptive_continuation_payload(start: np.ndarray, end: np.ndarray, initial_step: float, minimum_step: float, maximum_step: float, predictor_tolerance: float) -> dict[str, object]:
    result = continue_roots_adaptive(start, end, initial_step=initial_step, minimum_step=minimum_step, maximum_step=maximum_step, predictor_tolerance=predictor_tolerance); payload = _base("adaptive"); payload.update({"status": result.status, "rejected_attempts": result.rejected_attempts, "minimum_step_size": result.minimum_step_size, "steps": [{"t": item.parameter, "step_size": item.step_size, "attempts": item.attempts, "roots": _complex_vector(item.roots), "predictor_residual": item.predictor_residual, "corrected_residual": item.corrected_residual, "minimum_derivative": item.minimum_derivative} for item in result.steps], "claims": {"theorem_claimed": result.theorem_claimed, "scientific_validation_claimed": result.scientific_validation_claimed}}); return payload


def inverse_design_payload(coefficients: np.ndarray, target_roots: np.ndarray, real_coefficients: bool, max_iterations: int, tolerance: float) -> dict[str, object]:
    result = inverse_design_roots(coefficients, target_roots, real_coefficients=real_coefficients, max_iterations=max_iterations, tolerance=tolerance); payload = _base("inverse-design"); payload.update({"status": result.status, "converged": result.converged, "root_error_norm": result.root_error_norm, "coefficients": _complex_vector(result.coefficients), "roots": _complex_vector(result.roots), "target_roots": _complex_vector(result.target_roots), "iterations": [{"iteration": item.iteration, "root_error_norm": item.root_error_norm, "update_norm": item.update_norm, "accepted_scale": item.accepted_scale, "linear_rank": item.linear_rank, "linear_condition_number": item.linear_condition_number, "max_root_residual": item.max_root_residual} for item in result.steps], "claims": {"theorem_claimed": result.theorem_claimed, "scientific_validation_claimed": result.scientific_validation_claimed}}); return payload


def _write(payload: dict[str, object], output: str | None) -> None:
    text = json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=False)
    if output: Path(output).write_text(text + "\n", encoding="utf-8")
    else: print(text)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Ω-ROOTFLOW-T∞ polynomial-root geometry engine"); sub = parser.add_subparsers(dest="command", required=True)
    def command(name: str, help_text: str): return sub.add_parser(name, help=help_text)
    p=command("analyze","root differential audit"); p.add_argument("--coeffs",required=True,type=_parse_coefficients); p.add_argument("--output")
    p=command("exact-audit","exact rational algebra audit"); p.add_argument("--coeffs",required=True,type=_parse_exact_coefficients); p.add_argument("--output")
    p=command("exact-multiplicity","exact multiplicity of a rational root"); p.add_argument("--coeffs",required=True,type=_parse_exact_coefficients); p.add_argument("--root",required=True); p.add_argument("--output")
    p=command("collision-tangent","generic double-root tangent space"); p.add_argument("--coeffs",required=True,type=_parse_coefficients); p.add_argument("--critical-root",required=True,type=complex); p.add_argument("--degrees",required=True,type=_parse_degrees); p.add_argument("--epsilon",type=float,default=1e-4); p.add_argument("--output")
    p=command("multiplicity-tangent","arbitrary multiplicity root stratum tangent space"); p.add_argument("--coeffs",required=True,type=_parse_coefficients); p.add_argument("--critical-root",required=True,type=complex); p.add_argument("--multiplicity",required=True,type=int); p.add_argument("--degrees",required=True,type=_parse_degrees); p.add_argument("--epsilon",type=float,default=1e-4); p.add_argument("--output")
    p=command("real-tangent","real-parameter tangent geometry of a multiplicity stratum"); p.add_argument("--coeffs",required=True,type=_parse_coefficients); p.add_argument("--critical-root",required=True,type=complex); p.add_argument("--multiplicity",required=True,type=int); p.add_argument("--degrees",required=True,type=_parse_degrees); p.add_argument("--output")
    p=command("unfolding","translation-normalized local versal unfolding"); p.add_argument("--coeffs",required=True,type=_parse_coefficients); p.add_argument("--critical-root",required=True,type=complex); p.add_argument("--multiplicity",required=True,type=int); p.add_argument("--degrees",required=True,type=_parse_degrees); p.add_argument("--direction",required=True,type=_parse_complex_vector); p.add_argument("--epsilon",type=float,default=1e-4); p.add_argument("--output")
    p=command("invariants","Vieta/Newton/residue audit"); p.add_argument("--coeffs",required=True,type=_parse_coefficients); p.add_argument("--output")
    p=command("discriminant","resultant discriminant audit"); p.add_argument("--coeffs",required=True,type=_parse_coefficients); p.add_argument("--output")
    p=command("collisions","single coefficient collision atlas"); p.add_argument("--coeffs",required=True,type=_parse_coefficients); p.add_argument("--coefficient-degree",required=True,type=int); p.add_argument("--output")
    p=command("kinematics","root parameter kinematics"); p.add_argument("--coeffs",required=True,type=_parse_coefficients); p.add_argument("--velocity",required=True,type=_parse_complex_vector); p.add_argument("--acceleration",type=_parse_complex_vector); p.add_argument("--delta",type=complex,default=0.0); p.add_argument("--output")
    for name,help_text in [("spectral","spectral cross-check"),("basis-atlas","basis conditioning"),("projective","projective roots")]: p=command(name,help_text); p.add_argument("--coeffs",required=True,type=_parse_coefficients); p.add_argument("--output")
    p=command("projective-flow-demo","projective degree flow"); p.add_argument("--samples",type=int,default=33); p.add_argument("--output")
    p=command("puiseux-demo","canonical Puiseux fit"); p.add_argument("--multiplicity",type=int,default=2); p.add_argument("--output")
    p=command("monodromy-demo","square-root monodromy"); p.add_argument("--samples",type=int,default=17); p.add_argument("--subdivisions",type=int,default=2); p.add_argument("--output")
    p=command("monodromy-group-demo","monodromy group closure"); p.add_argument("--output")
    p=command("hgfm-demo","spectral HGFM"); p.add_argument("--samples",type=int,default=17); p.add_argument("--output")
    p=command("continue","fixed-step continuation"); p.add_argument("--start",required=True,type=_parse_coefficients); p.add_argument("--end",required=True,type=_parse_coefficients); p.add_argument("--steps",type=int,default=32); p.add_argument("--output")
    p=command("adaptive","adaptive continuation"); p.add_argument("--start",required=True,type=_parse_coefficients); p.add_argument("--end",required=True,type=_parse_coefficients); p.add_argument("--initial-step",type=float,default=0.125); p.add_argument("--minimum-step",type=float,default=1e-5); p.add_argument("--maximum-step",type=float,default=0.25); p.add_argument("--predictor-tolerance",type=float,default=1e-3); p.add_argument("--output")
    p=command("inverse-design","fit coefficients to roots"); p.add_argument("--coeffs",required=True,type=_parse_coefficients); p.add_argument("--target-roots",required=True,type=_parse_roots); p.add_argument("--complex-coefficients",action="store_false",dest="real_coefficients"); p.set_defaults(real_coefficients=True); p.add_argument("--max-iterations",type=int,default=24); p.add_argument("--tolerance",type=float,default=1e-10); p.add_argument("--output")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args=build_parser().parse_args(argv)
    if args.command=="analyze": payload=analyze_payload(args.coeffs)
    elif args.command=="exact-audit": payload=exact_audit_payload(args.coeffs)
    elif args.command=="exact-multiplicity": payload=exact_multiplicity_payload(args.coeffs,args.root)
    elif args.command=="collision-tangent": payload=collision_tangent_payload(args.coeffs,args.critical_root,args.degrees,args.epsilon)
    elif args.command=="multiplicity-tangent": payload=multiplicity_tangent_payload(args.coeffs,args.critical_root,args.multiplicity,args.degrees,args.epsilon)
    elif args.command=="real-tangent": payload=real_tangent_payload(args.coeffs,args.critical_root,args.multiplicity,args.degrees)
    elif args.command=="unfolding": payload=unfolding_payload(args.coeffs,args.critical_root,args.multiplicity,args.degrees,args.direction,args.epsilon)
    elif args.command=="invariants": payload=invariant_payload(args.coeffs)
    elif args.command=="discriminant": payload=discriminant_payload(args.coeffs)
    elif args.command=="collisions": payload=collisions_payload(args.coeffs,args.coefficient_degree)
    elif args.command=="kinematics": payload=kinematics_payload(args.coeffs,args.velocity,args.acceleration,args.delta)
    elif args.command=="spectral": payload=spectral_payload(args.coeffs)
    elif args.command=="basis-atlas": payload=basis_atlas_payload(args.coeffs)
    elif args.command=="projective": payload=projective_payload(args.coeffs)
    elif args.command=="projective-flow-demo": payload=projective_flow_demo_payload(args.samples)
    elif args.command=="puiseux-demo": payload=puiseux_demo_payload(args.multiplicity)
    elif args.command=="monodromy-demo": payload=monodromy_demo_payload(args.samples,args.subdivisions)
    elif args.command=="monodromy-group-demo": payload=monodromy_group_demo_payload()
    elif args.command=="hgfm-demo": payload=hgfm_demo_payload(args.samples)
    elif args.command=="continue": payload=continuation_payload(args.start,args.end,args.steps)
    elif args.command=="adaptive": payload=adaptive_continuation_payload(args.start,args.end,args.initial_step,args.minimum_step,args.maximum_step,args.predictor_tolerance)
    elif args.command=="inverse-design": payload=inverse_design_payload(args.coeffs,args.target_roots,args.real_coefficients,args.max_iterations,args.tolerance)
    else: raise AssertionError("unreachable")
    _write(payload,args.output); return 0


if __name__ == "__main__": raise SystemExit(main())
