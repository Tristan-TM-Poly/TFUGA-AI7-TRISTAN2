from __future__ import annotations

from collections import deque
import json
import math
from typing import Iterable

from .formal import (
    build_p7_certificate,
    evaluate_expr,
    normalize_expr,
    variables_in_expr,
)


_COST_MODEL_ID = "omega-asm-superopt-structural-v1"
_COMMUTATIVE = {"add", "mul", "xor", "and", "or"}
_BINARY_COST = {
    "add": 1.0,
    "sub": 1.0,
    "mul": 3.0,
    "xor": 1.0,
    "and": 1.0,
    "or": 1.0,
    "shl": 1.0,
    "lshr": 1.0,
}
_UNARY_COST = {"not": 1.0, "neg": 1.0}


def _key(expr: dict[str, object]) -> str:
    return json.dumps(expr, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def _const(value: int, width: int) -> dict[str, object]:
    return {"op": "const", "value": value & ((1 << width) - 1)}


def _const_value(expr: dict[str, object]) -> int | None:
    return int(expr["value"]) if expr.get("op") == "const" else None


def _binary(op: str, left: dict[str, object], right: dict[str, object]) -> dict[str, object]:
    return {"op": op, "args": [left, right]}


def expression_cost(expr: object, width: int) -> float:
    normalized = normalize_expr(expr, width)
    op = str(normalized["op"])
    if op in {"var", "const"}:
        return 0.0
    if op in _UNARY_COST:
        return _UNARY_COST[op] + expression_cost(normalized["arg"], width)
    args = normalized["args"]
    assert isinstance(args, list)
    return _BINARY_COST[op] + expression_cost(args[0], width) + expression_cost(args[1], width)


def _root_rewrites(expr: dict[str, object], width: int) -> list[tuple[str, dict[str, object]]]:
    op = str(expr["op"])
    rows: list[tuple[str, dict[str, object]]] = []
    mask = (1 << width) - 1

    if op in _UNARY_COST:
        arg = expr["arg"]
        assert isinstance(arg, dict)
        value = _const_value(arg)
        if value is not None:
            rows.append((f"constant-fold-{op}", _const(evaluate_expr(expr, {}, width), width)))
        if op == "not" and arg.get("op") == "not":
            inner = arg["arg"]
            assert isinstance(inner, dict)
            rows.append(("double-not-elimination", inner))
        return rows

    if op not in _BINARY_COST:
        return rows
    args = expr["args"]
    assert isinstance(args, list)
    left, right = args
    assert isinstance(left, dict) and isinstance(right, dict)
    lv, rv = _const_value(left), _const_value(right)

    if lv is not None and rv is not None:
        rows.append((f"constant-fold-{op}", _const(evaluate_expr(expr, {}, width), width)))

    if op in _COMMUTATIVE and _key(left) > _key(right):
        rows.append((f"canonicalize-{op}", _binary(op, right, left)))

    if op in {"add", "sub", "xor", "or"} and rv == 0:
        rows.append((f"{op}-right-zero", left))
    if op in {"add", "xor", "or"} and lv == 0:
        rows.append((f"{op}-left-zero", right))
    if op == "mul" and rv == 1:
        rows.append(("mul-right-one", left))
    if op == "mul" and lv == 1:
        rows.append(("mul-left-one", right))
    if op == "mul" and (rv == 0 or lv == 0):
        rows.append(("mul-zero", _const(0, width)))
    if op == "and" and rv == mask:
        rows.append(("and-right-all-ones", left))
    if op == "and" and lv == mask:
        rows.append(("and-left-all-ones", right))
    if op == "shl" and rv == 0:
        rows.append(("shift-left-zero", left))
    if op == "lshr" and rv == 0:
        rows.append(("logical-shift-right-zero", left))

    if _key(left) == _key(right):
        if op in {"xor", "sub"}:
            rows.append((f"{op}-self-zero", _const(0, width)))
        if op in {"and", "or"}:
            rows.append((f"{op}-idempotent", left))
        if op == "add" and width > 1:
            rows.append(("add-self-to-shift", _binary("shl", left, _const(1, width))))

    # Multiplication by a power of two is a left shift under fixed-width modulo semantics.
    for constant, other, side in ((rv, left, "right"), (lv, right, "left")):
        if constant is None or constant <= 1:
            continue
        if constant & (constant - 1) == 0:
            shift = int(math.log2(constant))
            if shift < width:
                rows.append((f"mul-{side}-power2-to-shift", _binary("shl", other, _const(shift, width))))

    return rows


def one_step_rewrites(expr: object, width: int) -> list[tuple[str, dict[str, object]]]:
    normalized = normalize_expr(expr, width)
    rows = _root_rewrites(normalized, width)
    op = str(normalized["op"])
    if op in _UNARY_COST:
        arg = normalized["arg"]
        assert isinstance(arg, dict)
        for rule, child in one_step_rewrites(arg, width):
            rows.append((f"arg/{rule}", {"op": op, "arg": child}))
    elif op in _BINARY_COST:
        args = normalized["args"]
        assert isinstance(args, list)
        left, right = args
        assert isinstance(left, dict) and isinstance(right, dict)
        for rule, child in one_step_rewrites(left, width):
            rows.append((f"left/{rule}", _binary(op, child, right)))
        for rule, child in one_step_rewrites(right, width):
            rows.append((f"right/{rule}", _binary(op, left, child)))

    dedup: dict[str, tuple[str, dict[str, object]]] = {}
    for rule, candidate in rows:
        candidate = normalize_expr(candidate, width)
        if _key(candidate) != _key(normalized):
            dedup.setdefault(_key(candidate), (rule, candidate))
    return list(dedup.values())


def enumerate_rewrites(expr: object, width: int, *, max_candidates: int = 128) -> list[dict[str, object]]:
    if isinstance(max_candidates, bool) or not isinstance(max_candidates, int) or max_candidates < 1:
        raise ValueError("max_candidates must be a positive integer")
    root = normalize_expr(expr, width)
    queue = deque([(root, tuple())])
    seen = {_key(root)}
    rows: list[dict[str, object]] = []
    while queue and len(rows) < max_candidates:
        current, trace = queue.popleft()
        rows.append({"expression": current, "trace": list(trace)})
        if len(rows) >= max_candidates:
            break
        for rule, candidate in one_step_rewrites(current, width):
            key = _key(candidate)
            if key in seen:
                continue
            seen.add(key)
            queue.append((candidate, trace + (rule,)))
            if len(seen) >= max_candidates:
                break
    return rows


def certify_rewrite(
    original: object,
    candidate: object,
    width: int,
    *,
    max_states: int = 1_000_000,
) -> dict[str, object]:
    spec = {
        "name": "superopt-candidate-equivalence",
        "width": width,
        "lhs": normalize_expr(original, width),
        "rhs": normalize_expr(candidate, width),
    }
    certificate = build_p7_certificate(spec, max_states=max_states)
    return {
        "obligation_id": certificate["obligation_id"],
        "verification_status": certificate["verification_status"],
        "accepted_equivalent": certificate["accepted_equivalent"],
        "kernel_checked": certificate["kernel_checked"],
        "states_total": certificate["exhaustive_evidence"]["states_total"],
        "states_checked": certificate["exhaustive_evidence"]["states_checked"],
        "counterexample": certificate["exhaustive_evidence"]["counterexample"],
    }


def normalize_superopt_spec(spec: object) -> dict[str, object]:
    if not isinstance(spec, dict):
        raise ValueError("superoptimizer spec must be an object")
    width = spec.get("width")
    if isinstance(width, bool) or not isinstance(width, int) or not 1 <= width <= 64:
        raise ValueError("width must be an integer in [1, 64]")
    name = spec.get("name", "anonymous-superopt")
    if not isinstance(name, str) or not name.strip():
        raise ValueError("name must be a non-empty string")
    if "expression" not in spec:
        raise ValueError("superoptimizer spec requires expression")
    expression = normalize_expr(spec["expression"], width)
    return {
        "name": name.strip(),
        "width": width,
        "expression": expression,
        "variables": list(variables_in_expr(expression)),
    }


def superoptimize(
    spec: object,
    *,
    max_candidates: int = 128,
    max_states: int = 1_000_000,
) -> dict[str, object]:
    normalized = normalize_superopt_spec(spec)
    width = int(normalized["width"])
    original = normalized["expression"]
    assert isinstance(original, dict)
    original_key = _key(original)
    original_cost = expression_cost(original, width)
    candidates = enumerate_rewrites(original, width, max_candidates=max_candidates)

    rows: list[dict[str, object]] = []
    for item in candidates:
        expression = item["expression"]
        assert isinstance(expression, dict)
        cost = expression_cost(expression, width)
        if _key(expression) == original_key:
            proof = {
                "obligation_id": None,
                "verification_status": "reflexive_baseline",
                "accepted_equivalent": True,
                "kernel_checked": False,
                "states_total": None,
                "states_checked": None,
                "counterexample": None,
            }
        else:
            proof = certify_rewrite(original, expression, width, max_states=max_states)
        rows.append({
            "expression": expression,
            "trace": item["trace"],
            "structural_cost_units": cost,
            "cost_delta_from_original": cost - original_cost,
            "proof": proof,
        })

    accepted = [row for row in rows if row["proof"]["accepted_equivalent"] is True]
    best = min(accepted, key=lambda row: (row["structural_cost_units"], _key(row["expression"])))
    return {
        "schema_version": 1,
        "evidence_level": "bounded-proof-first-superoptimization",
        "name": normalized["name"],
        "width": width,
        "variables": normalized["variables"],
        "claim_scope": "fixed_width_bitvector_structural_optimization_only",
        "authority": "review_only",
        "cost_model": {
            "id": _COST_MODEL_ID,
            "calibrated": False,
            "units": "structural_cost_units",
            "runtime_cycles": False,
        },
        "search_bounds": {
            "max_candidates": max_candidates,
            "max_states_per_proof": max_states,
            "candidate_count": len(rows),
            "accepted_equivalent_count": len(accepted),
        },
        "original": {"expression": original, "structural_cost_units": original_cost},
        "best": best,
        "improved_structural_cost": best["structural_cost_units"] < original_cost,
        "candidates": rows,
        "selection_contract": {
            "equivalence_before_selection": True,
            "unverified_candidate_can_win": False,
            "runtime_speed_claim_allowed": False,
            "automatic_authority_promotion": False,
        },
    }
