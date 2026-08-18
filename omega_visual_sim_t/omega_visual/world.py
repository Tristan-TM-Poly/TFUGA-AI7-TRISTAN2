from __future__ import annotations

import hashlib
import json
from copy import deepcopy
from typing import Any


WORLD_SCHEMA_VERSION = "0.2"
ATTACHMENT_PROTOCOL = "OMEGA-SIM-ATTACH/0.2"
SCIENTIFIC_STATUSES = {
    "ARTISTIC",
    "CONCEPTUAL",
    "SCHEMATIC",
    "DATA_DRIVEN",
    "SIMULATED",
    "EXPERIMENTAL",
    "VERIFIED",
}
EXECUTION_TARGETS = {"client", "remote", "hybrid"}
FIDELITY_LEVELS = {"toy", "analytical", "rom", "surrogate", "full_solver"}


class WorldSpecError(ValueError):
    """Raised when an ExecutableWorld contract is unsafe or internally inconsistent."""


def _canonical_bytes(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")


def _sha256(value: Any) -> str:
    return hashlib.sha256(_canonical_bytes(value)).hexdigest()


def _require_mapping(value: Any, path: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise WorldSpecError(f"{path} must be an object")
    return value


def _require_list(value: Any, path: str, *, allow_empty: bool = True) -> list[Any]:
    if not isinstance(value, list):
        raise WorldSpecError(f"{path} must be a list")
    if not allow_empty and not value:
        raise WorldSpecError(f"{path} must not be empty")
    return value


def _require_text(value: Any, path: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise WorldSpecError(f"{path} must be a non-empty string")
    return value.strip()


def _validate_quantity_records(records: Any, path: str) -> set[str]:
    values = _require_list(records, path, allow_empty=False)
    identifiers: set[str] = set()
    for index, raw in enumerate(values):
        record = _require_mapping(raw, f"{path}[{index}]")
        identifier = _require_text(record.get("id"), f"{path}[{index}].id")
        _require_text(record.get("quantity"), f"{path}[{index}].quantity")
        _require_text(record.get("unit"), f"{path}[{index}].unit")
        if identifier in identifiers:
            raise WorldSpecError(f"duplicate quantity id: {identifier}")
        identifiers.add(identifier)
    return identifiers


def validate_executable_world(spec: dict[str, Any]) -> dict[str, Any]:
    """Validate and return a defensive copy of an ExecutableWorld specification.

    The validator is deliberately dependency-free so the web/runtime ABI remains usable
    without a JSON-schema package. The checked-in JSON schema is the interchange contract;
    this function adds semantic gates such as unit presence and reference integrity.
    """

    root = deepcopy(_require_mapping(spec, "world_spec"))
    if root.get("schema_version") != WORLD_SCHEMA_VERSION:
        raise WorldSpecError(f"schema_version must be {WORLD_SCHEMA_VERSION}")

    world = _require_mapping(root.get("world"), "world")
    _require_text(world.get("id"), "world.id")
    _require_text(world.get("title"), "world.title")
    status = _require_text(world.get("scientific_status"), "world.scientific_status")
    if status not in SCIENTIFIC_STATUSES:
        raise WorldSpecError(f"unsupported scientific status: {status}")
    _require_list(world.get("assumptions"), "world.assumptions")
    _require_text(world.get("domain_of_validity"), "world.domain_of_validity")

    state_ids = _validate_quantity_records(root.get("state"), "state")
    observable_ids = _validate_quantity_records(root.get("observables"), "observables")
    known_quantities = state_ids | observable_ids

    engines = _require_list(root.get("engines"), "engines", allow_empty=False)
    engine_ids: set[str] = set()
    for index, raw in enumerate(engines):
        engine = _require_mapping(raw, f"engines[{index}]")
        engine_id = _require_text(engine.get("id"), f"engines[{index}].id")
        if engine_id in engine_ids:
            raise WorldSpecError(f"duplicate engine id: {engine_id}")
        engine_ids.add(engine_id)
        _require_text(engine.get("capability"), f"engines[{index}].capability")
        execution = _require_mapping(engine.get("execution"), f"engines[{index}].execution")
        target = _require_text(execution.get("target"), f"engines[{index}].execution.target")
        if target not in EXECUTION_TARGETS:
            raise WorldSpecError(f"unsupported execution target: {target}")
        if not isinstance(execution.get("deterministic"), bool):
            raise WorldSpecError(f"engines[{index}].execution.deterministic must be boolean")
        fidelity = _require_text(engine.get("fidelity"), f"engines[{index}].fidelity")
        if fidelity not in FIDELITY_LEVELS:
            raise WorldSpecError(f"unsupported fidelity level: {fidelity}")
        for field in ("inputs", "outputs"):
            refs = _require_list(engine.get(field), f"engines[{index}].{field}")
            for ref in refs:
                if not isinstance(ref, str) or not ref.strip():
                    raise WorldSpecError(f"engines[{index}].{field} references must be strings")

    views = _require_list(root.get("views"), "views", allow_empty=False)
    view_ids: set[str] = set()
    for index, raw in enumerate(views):
        view = _require_mapping(raw, f"views[{index}]")
        view_id = _require_text(view.get("id"), f"views[{index}].id")
        if view_id in view_ids:
            raise WorldSpecError(f"duplicate view id: {view_id}")
        view_ids.add(view_id)
        _require_text(view.get("kind"), f"views[{index}].kind")
        refs = _require_list(view.get("observables"), f"views[{index}].observables", allow_empty=False)
        unknown = sorted(set(refs) - known_quantities)
        if unknown:
            raise WorldSpecError(f"view {view_id} references unknown quantities: {', '.join(unknown)}")
        _require_list(view.get("transformations"), f"views[{index}].transformations")

    uncertainty = _require_mapping(root.get("uncertainty"), "uncertainty")
    for key in ("parameter", "measurement", "numerical", "structural", "extrapolation"):
        _require_text(uncertainty.get(key), f"uncertainty.{key}")

    evidence = _require_list(root.get("evidence"), "evidence")
    if status == "VERIFIED" and not evidence:
        raise WorldSpecError("VERIFIED status requires at least one evidence record")

    controls = root.get("controls", [])
    _require_list(controls, "controls")
    root["controls"] = controls
    root.setdefault("known_limits", [])
    _require_list(root["known_limits"], "known_limits")
    return root


def visual_spec_to_world(visual_spec: dict[str, Any]) -> dict[str, Any]:
    """Lift the R0.1 VisualSpec oscillator into the R0.2 ExecutableWorld ABI."""

    model = _require_mapping(visual_spec.get("model"), "VisualSpec.model")
    if model.get("type") != "damped_harmonic_oscillator":
        raise WorldSpecError("VisualSpec adapter currently supports damped_harmonic_oscillator")
    units = _require_mapping(model.get("units"), "VisualSpec.model.units")
    expected = {"mass": "kg", "stiffness": "N/m", "damping": "N*s/m", "displacement": "m"}
    if units != expected:
        raise WorldSpecError(f"VisualSpec units must equal {expected}")

    parameters = _require_mapping(model.get("parameters"), "VisualSpec.model.parameters")
    title = str(visual_spec.get("visual", {}).get("title", "Damped harmonic oscillator"))
    world = {
        "schema_version": WORLD_SCHEMA_VERSION,
        "world": {
            "id": "damped-harmonic-oscillator",
            "title": title,
            "scientific_status": "SIMULATED",
            "assumptions": [
                "linear restoring force",
                "linear viscous damping",
                "constant coefficients",
                "underdamped analytic regime",
            ],
            "domain_of_validity": "single-degree-of-freedom linear underdamped oscillator",
        },
        "state": [
            {"id": "time", "quantity": "time", "unit": "s"},
            {"id": "displacement", "quantity": "displacement", "unit": "m"},
            {"id": "velocity", "quantity": "velocity", "unit": "m/s"},
        ],
        "observables": [
            {"id": "displacement_obs", "quantity": "displacement", "unit": "m"},
            {"id": "velocity_obs", "quantity": "velocity", "unit": "m/s"},
        ],
        "engines": [
            {
                "id": "analytic-underdamped-oscillator",
                "capability": "solve_ode_analytic",
                "execution": {"target": "client", "deterministic": True},
                "fidelity": "analytical",
                "inputs": ["time", "displacement", "velocity"],
                "outputs": ["displacement_obs", "velocity_obs"],
            }
        ],
        "views": [
            {
                "id": "schematic-motion",
                "kind": "schematic",
                "observables": ["displacement_obs"],
                "transformations": ["normalized schematic geometry"],
            },
            {
                "id": "phase-state",
                "kind": "phase",
                "observables": ["displacement_obs", "velocity_obs"],
                "transformations": [],
            },
        ],
        "controls": [
            {"id": "mass_kg", "value": parameters.get("mass_kg"), "unit": "kg"},
            {"id": "stiffness_n_m", "value": parameters.get("stiffness_n_m"), "unit": "N/m"},
            {"id": "damping_n_s_m", "value": parameters.get("damping_n_s_m"), "unit": "N*s/m"},
            {"id": "initial_displacement_m", "value": parameters.get("initial_displacement_m"), "unit": "m"},
            {"id": "initial_velocity_m_s", "value": parameters.get("initial_velocity_m_s", 0.0), "unit": "m/s"},
        ],
        "uncertainty": {
            "parameter": "unquantified",
            "measurement": "not_applicable_without_experiment",
            "numerical": "analytic_solution_sampling_only",
            "structural": "unquantified",
            "extrapolation": "outside_domain_not_supported",
        },
        "evidence": [],
        "known_limits": [
            "no experimental calibration",
            "uncertainty is not quantified",
            "schematic geometry is not to scale",
        ],
        "source": {
            "kind": "VisualSpec",
            "sha256": _sha256(visual_spec),
        },
    }
    return validate_executable_world(world)


def compile_sim_capsule(world_spec: dict[str, Any], *, seed: int = 0) -> dict[str, Any]:
    """Compile an ExecutableWorld into a web-attachable, content-addressed SimCapsule."""

    world = validate_executable_world(world_spec)
    world_sha256 = _sha256(world)
    run_identity = {"world_sha256": world_sha256, "seed": int(seed)}
    targets = {engine["execution"]["target"] for engine in world["engines"]}
    preferred_target = next(iter(targets)) if len(targets) == 1 else "hybrid"
    unquantified = sorted(
        key for key, value in world["uncertainty"].items() if "unquantified" in value.lower()
    )
    residues = list(world.get("known_limits", []))
    if unquantified:
        residues.append("unquantified uncertainty: " + ", ".join(unquantified))

    return {
        "schema_version": WORLD_SCHEMA_VERSION,
        "protocol": ATTACHMENT_PROTOCOL,
        "capsule_id": f"{world['world']['id']}@{world_sha256[:16]}",
        "world_sha256": world_sha256,
        "run_sha256": _sha256(run_identity),
        "world": world,
        "execution": {
            "preferred_target": preferred_target,
            "streaming": {"state_stream": True, "view_stream": True},
            "engines": [engine["id"] for engine in world["engines"]],
            "fidelity_levels": sorted({engine["fidelity"] for engine in world["engines"]}),
        },
        "attachment": {
            "slot": "SimSlot",
            "actions": ["inspect", "fork", "compare", "reset"],
            "controls": deepcopy(world.get("controls", [])),
            "views": [
                {"id": view["id"], "kind": view["kind"], "observables": list(view["observables"])}
                for view in world["views"]
            ],
        },
        "reproducibility": {
            "seed": int(seed),
            "content_addressed": True,
            "same_world_hash_means_same_world_contract": True,
        },
        "oak": {
            "scientific_status": world["world"]["scientific_status"],
            "simulation_is_proof": False,
            "visualization_is_truth": False,
            "evidence_count": len(world["evidence"]),
            "residues": residues,
        },
    }
