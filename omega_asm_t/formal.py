from __future__ import annotations

import hashlib
import itertools
import json
import math
import re
from typing import Any


_VAR_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")
_BINARY_OPS = {
    "add": "bvadd",
    "sub": "bvsub",
    "mul": "bvmul",
    "xor": "bvxor",
    "and": "bvand",
    "or": "bvor",
    "shl": "bvshl",
    "lshr": "bvlshr",
}
_UNARY_OPS = {"not": "bvnot", "neg": "bvneg"}


def _validate_width(width: object) -> int:
    if isinstance(width, bool) or not isinstance(width, int) or not 1 <= width <= 64:
        raise ValueError("bit-vector width must be an integer in [1, 64]")
    return width


def normalize_expr(expr: object, width: int) -> dict[str, object]:
    width = _validate_width(width)
    if not isinstance(expr, dict):
        raise ValueError("expression must be a JSON object")
    op = expr.get("op")
    if op == "var":
        name = expr.get("name")
        if not isinstance(name, str) or not _VAR_RE.fullmatch(name):
            raise ValueError("variable name must match [A-Za-z_][A-Za-z0-9_]*")
        return {"op": "var", "name": name}
    if op == "const":
        value = expr.get("value")
        if isinstance(value, bool) or not isinstance(value, int):
            raise ValueError("constant value must be an integer")
        return {"op": "const", "value": value & ((1 << width) - 1)}
    if op in _UNARY_OPS:
        if "arg" not in expr:
            raise ValueError(f"{op} expression requires arg")
        return {"op": op, "arg": normalize_expr(expr["arg"], width)}
    if op in _BINARY_OPS:
        args = expr.get("args")
        if not isinstance(args, list) or len(args) != 2:
            raise ValueError(f"{op} expression requires exactly two args")
        return {
            "op": op,
            "args": [normalize_expr(args[0], width), normalize_expr(args[1], width)],
        }
    raise ValueError(f"unsupported bit-vector op: {op!r}")


def _collect_variables(expr: dict[str, object], result: set[str]) -> None:
    op = expr["op"]
    if op == "var":
        result.add(str(expr["name"]))
    elif op in _UNARY_OPS:
        _collect_variables(expr["arg"], result)  # type: ignore[arg-type]
    elif op in _BINARY_OPS:
        args = expr["args"]
        assert isinstance(args, list)
        _collect_variables(args[0], result)
        _collect_variables(args[1], result)


def variables_in_expr(expr: dict[str, object]) -> tuple[str, ...]:
    result: set[str] = set()
    _collect_variables(expr, result)
    return tuple(sorted(result))


def normalize_equivalence_spec(spec: object) -> dict[str, object]:
    if not isinstance(spec, dict):
        raise ValueError("equivalence spec must be a JSON object")
    width = _validate_width(spec.get("width"))
    name = spec.get("name", "anonymous-equivalence")
    if not isinstance(name, str) or not name.strip():
        raise ValueError("spec name must be a non-empty string")
    if "lhs" not in spec or "rhs" not in spec:
        raise ValueError("equivalence spec requires lhs and rhs")
    lhs = normalize_expr(spec["lhs"], width)
    rhs = normalize_expr(spec["rhs"], width)
    variables = tuple(sorted(set(variables_in_expr(lhs)) | set(variables_in_expr(rhs))))
    if len(variables) > 16:
        raise ValueError("at most 16 distinct variables are supported in R2 P7")
    return {"name": name.strip(), "width": width, "lhs": lhs, "rhs": rhs, "variables": list(variables)}


def evaluate_expr(expr: dict[str, object], env: dict[str, int], width: int) -> int:
    width = _validate_width(width)
    mask = (1 << width) - 1
    op = expr["op"]
    if op == "var":
        name = str(expr["name"])
        if name not in env:
            raise ValueError(f"missing variable value: {name}")
        value = env[name]
        if isinstance(value, bool) or not isinstance(value, int):
            raise ValueError(f"variable {name} must map to an integer")
        return value & mask
    if op == "const":
        return int(expr["value"]) & mask
    if op in _UNARY_OPS:
        arg = evaluate_expr(expr["arg"], env, width)  # type: ignore[arg-type]
        if op == "not":
            return (~arg) & mask
        return (-arg) & mask

    args = expr["args"]
    assert isinstance(args, list)
    left = evaluate_expr(args[0], env, width)
    right = evaluate_expr(args[1], env, width)
    if op == "add":
        return (left + right) & mask
    if op == "sub":
        return (left - right) & mask
    if op == "mul":
        return (left * right) & mask
    if op == "xor":
        return (left ^ right) & mask
    if op == "and":
        return (left & right) & mask
    if op == "or":
        return (left | right) & mask
    if op == "shl":
        return 0 if right >= width else (left << right) & mask
    if op == "lshr":
        return 0 if right >= width else left >> right
    raise AssertionError(op)


def _smt_expr(expr: dict[str, object], width: int) -> str:
    op = expr["op"]
    if op == "var":
        return str(expr["name"])
    if op == "const":
        return f"(_ bv{int(expr['value'])} {width})"
    if op in _UNARY_OPS:
        return f"({_UNARY_OPS[op]} {_smt_expr(expr['arg'], width)})"  # type: ignore[arg-type]
    args = expr["args"]
    assert isinstance(args, list)
    return f"({_BINARY_OPS[op]} {_smt_expr(args[0], width)} {_smt_expr(args[1], width)})"


def obligation_id(spec: object) -> str:
    normalized = normalize_equivalence_spec(spec)
    payload = json.dumps(normalized, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def build_equivalence_obligation(spec: object) -> dict[str, object]:
    normalized = normalize_equivalence_spec(spec)
    width = int(normalized["width"])
    variables = normalized["variables"]
    assert isinstance(variables, list)
    declarations = [f"(declare-fun {name} () (_ BitVec {width}))" for name in variables]
    lhs = normalized["lhs"]
    rhs = normalized["rhs"]
    assert isinstance(lhs, dict) and isinstance(rhs, dict)
    oid = obligation_id(normalized)
    lines = [
        "; Ω-ASM-T bounded equivalence obligation",
        f"; obligation_id: {oid}",
        "(set-logic QF_BV)",
        *declarations,
        f"(assert (not (= {_smt_expr(lhs, width)} {_smt_expr(rhs, width)})))",
        "(check-sat)",
    ]
    return {
        "schema_version": 1,
        "evidence_level": "P7-bounded-equivalence-obligation",
        "obligation_id": oid,
        "name": normalized["name"],
        "width": width,
        "variables": variables,
        "lhs": lhs,
        "rhs": rhs,
        "semantics": "fixed_width_unsigned_bitvector_modulo_2^width",
        "claim_scope": "this_normalized_bitvector_statement_only",
        "smt_logic": "QF_BV",
        "smt2": "\n".join(lines) + "\n",
    }


def exhaustive_verify(spec: object, *, max_states: int = 1_000_000) -> dict[str, object]:
    if isinstance(max_states, bool) or not isinstance(max_states, int) or max_states < 1:
        raise ValueError("max_states must be a positive integer")
    normalized = normalize_equivalence_spec(spec)
    width = int(normalized["width"])
    variables = normalized["variables"]
    lhs = normalized["lhs"]
    rhs = normalized["rhs"]
    assert isinstance(variables, list) and isinstance(lhs, dict) and isinstance(rhs, dict)
    domain_size = 1 << width
    total_states = domain_size ** len(variables)
    if total_states > max_states:
        return {
            "status": "not_run",
            "complete": False,
            "states_total": total_states,
            "states_checked": 0,
            "max_states": max_states,
            "counterexample": None,
            "lhs_value": None,
            "rhs_value": None,
        }

    checked = 0
    for values in itertools.product(range(domain_size), repeat=len(variables)):
        env = dict(zip((str(name) for name in variables), values))
        left = evaluate_expr(lhs, env, width)
        right = evaluate_expr(rhs, env, width)
        checked += 1
        if left != right:
            return {
                "status": "counterexample",
                "complete": True,
                "states_total": total_states,
                "states_checked": checked,
                "max_states": max_states,
                "counterexample": env,
                "lhs_value": left,
                "rhs_value": right,
            }
    return {
        "status": "equivalent",
        "complete": True,
        "states_total": total_states,
        "states_checked": checked,
        "max_states": max_states,
        "counterexample": None,
        "lhs_value": None,
        "rhs_value": None,
    }


def parse_solver_status(text: str | None) -> str | None:
    if text is None:
        return None
    for line in text.splitlines():
        cleaned = line.strip().lower()
        if not cleaned or cleaned.startswith(";") or cleaned.startswith("#"):
            continue
        if cleaned in {"sat", "unsat", "unknown"}:
            return cleaned
    return "invalid"


def _transcript_hash(text: str | None) -> str | None:
    if text is None:
        return None
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def build_p7_certificate(
    spec: object,
    *,
    solver_text: str | None = None,
    solver_name: str | None = None,
    solver_version: str | None = None,
    max_states: int = 1_000_000,
) -> dict[str, object]:
    obligation = build_equivalence_obligation(spec)
    exhaustive = exhaustive_verify(spec, max_states=max_states)
    solver_status = parse_solver_status(solver_text)

    exhaustive_status = exhaustive["status"]
    if exhaustive_status == "counterexample" and solver_status == "unsat":
        verification_status = "evidence_conflict"
    elif exhaustive_status == "counterexample":
        verification_status = "refuted_exhaustive"
    elif exhaustive_status == "equivalent" and solver_status == "unsat":
        verification_status = "dual_verified_bounded"
    elif exhaustive_status == "equivalent" and solver_status == "sat":
        verification_status = "evidence_conflict"
    elif exhaustive_status == "equivalent":
        verification_status = "exhaustive_verified_bounded"
    elif solver_status == "unsat":
        verification_status = "solver_unsat_observed"
    elif solver_status == "sat":
        verification_status = "solver_sat_observed"
    else:
        verification_status = "unverified"

    accepted_equivalent = verification_status in {
        "dual_verified_bounded",
        "exhaustive_verified_bounded",
    }
    return {
        "schema_version": 1,
        "evidence_level": "P7-bounded-equivalence-certificate",
        "obligation_id": obligation["obligation_id"],
        "name": obligation["name"],
        "width": obligation["width"],
        "variables": obligation["variables"],
        "verification_status": verification_status,
        "accepted_equivalent": accepted_equivalent,
        "kernel_checked": False,
        "authority": "review_only",
        "claim_scope": "fixed_width_bitvector_semantics_only",
        "semantics": obligation["semantics"],
        "exhaustive_evidence": exhaustive,
        "solver_evidence": {
            "status": solver_status,
            "name": solver_name,
            "version": solver_version,
            "transcript_sha256": _transcript_hash(solver_text),
            "transcript_present": solver_text is not None,
            "solver_text_alone_grants_acceptance": False,
        },
        "obligation": obligation,
        "limitations": [
            "certificate scope is fixed-width bit-vector semantics only",
            "this does not model C/C++ undefined behavior or implementation-defined behavior",
            "this does not model floating-point semantics",
            "solver text alone is observational evidence unless independently replayed/checked",
            "kernel_checked remains false in this R2 implementation",
            "no benchmark or formal result grants automatic merge/publication authority",
        ],
    }
