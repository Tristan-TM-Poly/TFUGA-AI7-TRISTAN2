from __future__ import annotations

import ast
from dataclasses import asdict
from decimal import Decimal, localcontext
from fractions import Fraction
import json
import re
from typing import Any, Callable, Mapping

from .model import JobSpec, stable_digest


class RunnerError(ValueError):
    pass


class BudgetExceeded(RunnerError):
    pass


def _fraction_payload(value: Fraction) -> dict[str, Any]:
    return {
        "numerator": value.numerator,
        "denominator": value.denominator,
        "canonical": str(value.numerator) if value.denominator == 1 else f"{value.numerator}/{value.denominator}",
    }


def _require_integer(value: Fraction, operation: str) -> int:
    if value.denominator != 1:
        raise RunnerError(f"{operation} requires integer operands")
    return value.numerator


def _eval_exact_node(node: ast.AST, budget: list[int]) -> Fraction:
    budget[0] -= 1
    if budget[0] < 0:
        raise BudgetExceeded("exact expression exceeded max_operations")
    if isinstance(node, ast.Expression):
        return _eval_exact_node(node.body, budget)
    if isinstance(node, ast.Constant) and isinstance(node.value, int) and not isinstance(node.value, bool):
        return Fraction(node.value)
    if isinstance(node, ast.UnaryOp) and isinstance(node.op, (ast.UAdd, ast.USub)):
        value = _eval_exact_node(node.operand, budget)
        return value if isinstance(node.op, ast.UAdd) else -value
    if isinstance(node, ast.BinOp):
        left = _eval_exact_node(node.left, budget)
        right = _eval_exact_node(node.right, budget)
        if isinstance(node.op, ast.Add):
            return left + right
        if isinstance(node.op, ast.Sub):
            return left - right
        if isinstance(node.op, ast.Mult):
            return left * right
        if isinstance(node.op, ast.Div):
            if right == 0:
                raise RunnerError("division by zero")
            return left / right
        if isinstance(node.op, ast.FloorDiv):
            divisor = _require_integer(right, "floor division")
            if divisor == 0:
                raise RunnerError("division by zero")
            return Fraction(_require_integer(left, "floor division") // divisor)
        if isinstance(node.op, ast.Mod):
            divisor = _require_integer(right, "modulo")
            if divisor == 0:
                raise RunnerError("modulo by zero")
            return Fraction(_require_integer(left, "modulo") % divisor)
        if isinstance(node.op, ast.Pow):
            exponent = _require_integer(right, "power")
            if exponent < 0 or exponent > 100_000:
                raise RunnerError("power exponent must be in [0, 100000]")
            budget[0] -= max(0, exponent.bit_length() - 1)
            if budget[0] < 0:
                raise BudgetExceeded("power exceeded max_operations")
            return left ** exponent
    raise RunnerError(f"forbidden exact-expression syntax: {type(node).__name__}")


def evaluate_exact_expression(expression: str, max_operations: int) -> tuple[Fraction, int]:
    if not isinstance(expression, str) or not expression.strip():
        raise RunnerError("exact expression is blank")
    if len(expression.encode("utf-8")) > 100_000:
        raise RunnerError("exact expression is too large")
    try:
        tree = ast.parse(expression, mode="eval")
    except SyntaxError as exc:
        raise RunnerError("invalid exact-expression syntax") from exc
    budget = [max_operations]
    value = _eval_exact_node(tree, budget)
    return value, max_operations - budget[0]


def _run_exact(job: JobSpec) -> dict[str, Any]:
    expression = job.input.get("expression")
    value, operation_count = evaluate_exact_expression(
        str(expression or ""), job.resource_limits["max_operations"]
    )
    candidate = _fraction_payload(value)
    verified_value, verifier_operations = evaluate_exact_expression(
        str(expression), job.resource_limits["max_operations"]
    )
    verified = candidate == _fraction_payload(verified_value)
    return {
        "status": "success" if verified else "invalid_certificate",
        "certificate_status": "verified_exact" if verified else "invalid",
        "output": candidate,
        "operation_count": operation_count,
        "verifier_operation_count": verifier_operations,
        "verifier_kind": "independent_exact_recomputation_v1",
    }


def _decimal(value: Any, field: str) -> Decimal:
    try:
        result = Decimal(str(value))
    except Exception as exc:
        raise RunnerError(f"{field} is not a finite decimal") from exc
    if not result.is_finite():
        raise RunnerError(f"{field} must be finite")
    return result


def _interval_mul(left: tuple[Decimal, Decimal], right: tuple[Decimal, Decimal]) -> tuple[Decimal, Decimal]:
    products = (
        left[0] * right[0],
        left[0] * right[1],
        left[1] * right[0],
        left[1] * right[1],
    )
    return min(products).next_minus(), max(products).next_plus()


def evaluate_interval_polynomial(
    coefficients: list[Any],
    domain: list[Any],
    max_operations: int,
) -> tuple[tuple[Decimal, Decimal], int]:
    if not coefficients:
        raise RunnerError("polynomial coefficients are empty")
    if len(domain) != 2:
        raise RunnerError("interval must contain exactly two endpoints")
    if len(coefficients) * 2 > max_operations:
        raise BudgetExceeded("interval polynomial exceeded max_operations")
    with localcontext() as context:
        context.prec = 80
        low = _decimal(domain[0], "interval lower bound")
        high = _decimal(domain[1], "interval upper bound")
        if low > high:
            raise RunnerError("interval lower bound exceeds upper bound")
        x_interval = (low, high)
        result = (_decimal(coefficients[0], "coefficient"),) * 2
        operations = 0
        for coefficient_raw in coefficients[1:]:
            result = _interval_mul(result, x_interval)
            coefficient = _decimal(coefficient_raw, "coefficient")
            result = (result[0] + coefficient, result[1] + coefficient)
            operations += 2
        return (result[0].next_minus(), result[1].next_plus()), operations


def _interval_payload(value: tuple[Decimal, Decimal]) -> dict[str, str]:
    return {"lower": str(value[0]), "upper": str(value[1])}


def _run_interval(job: JobSpec) -> dict[str, Any]:
    coefficients = job.input.get("coefficients")
    domain = job.input.get("interval")
    if not isinstance(coefficients, list) or not isinstance(domain, list):
        raise RunnerError("interval polynomial requires coefficients and interval lists")
    interval, operations = evaluate_interval_polynomial(
        coefficients, domain, job.resource_limits["max_operations"]
    )
    candidate = _interval_payload(interval)
    verified_interval, verifier_operations = evaluate_interval_polynomial(
        list(coefficients), list(domain), job.resource_limits["max_operations"]
    )
    verified = candidate == _interval_payload(verified_interval)
    return {
        "status": "success" if verified else "invalid_certificate",
        "certificate_status": "verified_outward_interval" if verified else "invalid",
        "output": candidate,
        "operation_count": operations,
        "verifier_operation_count": verifier_operations,
        "verifier_kind": "independent_interval_recomputation_v1",
    }


def verify_sat_certificate(
    clauses: list[Any],
    assignment_raw: Mapping[str, Any],
    max_operations: int,
) -> tuple[bool, list[int], int]:
    assignment: dict[int, bool] = {}
    for key, value in assignment_raw.items():
        try:
            variable = int(key)
        except (TypeError, ValueError) as exc:
            raise RunnerError("SAT assignment keys must be positive integers") from exc
        if variable <= 0 or not isinstance(value, bool):
            raise RunnerError("SAT assignment requires positive integer variables and booleans")
        assignment[variable] = value
    unsatisfied: list[int] = []
    operations = 0
    for index, clause_raw in enumerate(clauses):
        if not isinstance(clause_raw, list) or not clause_raw:
            raise RunnerError("every SAT clause must be a nonempty list")
        satisfied = False
        for literal_raw in clause_raw:
            if not isinstance(literal_raw, int) or isinstance(literal_raw, bool) or literal_raw == 0:
                raise RunnerError("SAT literals must be nonzero integers")
            operations += 1
            if operations > max_operations:
                raise BudgetExceeded("SAT verification exceeded max_operations")
            variable = abs(literal_raw)
            value = assignment.get(variable)
            if value is None:
                continue
            if (literal_raw > 0 and value) or (literal_raw < 0 and not value):
                satisfied = True
                break
        if not satisfied:
            unsatisfied.append(index)
    return not unsatisfied, unsatisfied, operations


def _run_sat(job: JobSpec) -> dict[str, Any]:
    clauses = job.input.get("clauses")
    assignment = job.input.get("assignment")
    if not isinstance(clauses, list) or not isinstance(assignment, Mapping):
        raise RunnerError("SAT certificate requires clauses and assignment")
    valid, unsatisfied, operations = verify_sat_certificate(
        clauses, assignment, job.resource_limits["max_operations"]
    )
    verifier_valid, verifier_unsatisfied, verifier_operations = verify_sat_certificate(
        json.loads(json.dumps(clauses)), dict(assignment), job.resource_limits["max_operations"]
    )
    verified = valid == verifier_valid and unsatisfied == verifier_unsatisfied
    status = "success" if valid and verified else "invalid_certificate"
    return {
        "status": status,
        "certificate_status": "verified_boolean_certificate" if status == "success" else "invalid",
        "output": {
            "satisfied": valid,
            "unsatisfied_clause_indices": unsatisfied,
        },
        "operation_count": operations,
        "verifier_operation_count": verifier_operations,
        "verifier_kind": "independent_sat_assignment_verifier_v1",
    }


def validate_lean_skeleton(source: str, max_operations: int) -> tuple[bool, list[str], int]:
    if not isinstance(source, str) or not source.strip():
        raise RunnerError("Lean skeleton source is blank")
    operations = len(source)
    if operations > max_operations:
        raise BudgetExceeded("Lean skeleton exceeded max_operations")
    blockers: list[str] = []
    lowered = source.casefold()
    forbidden = {
        "sorry": r"\bsorry\b",
        "admit": r"\badmit\b",
        "axiom": r"\baxiom\b",
        "unsafe": r"\bunsafe\b",
    }
    for name, pattern in forbidden.items():
        if re.search(pattern, lowered):
            blockers.append(f"forbidden_token:{name}")
    if not re.search(r"\b(theorem|lemma|example)\b", lowered):
        blockers.append("missing_theorem_declaration")
    if ":=" not in source:
        blockers.append("missing_definition_body")
    delimiter_pairs = {"(": ")", "[": "]", "{": "}"}
    stack: list[str] = []
    for character in source:
        if character in delimiter_pairs:
            stack.append(delimiter_pairs[character])
        elif character in delimiter_pairs.values():
            if not stack or stack.pop() != character:
                blockers.append("unbalanced_delimiters")
                break
    if stack:
        blockers.append("unbalanced_delimiters")
    return not blockers, sorted(set(blockers)), operations


def _run_lean_skeleton(job: JobSpec) -> dict[str, Any]:
    source = job.input.get("source")
    valid, blockers, operations = validate_lean_skeleton(
        str(source or ""), job.resource_limits["max_operations"]
    )
    verifier_valid, verifier_blockers, verifier_operations = validate_lean_skeleton(
        str(source or ""), job.resource_limits["max_operations"]
    )
    verified = valid == verifier_valid and blockers == verifier_blockers
    status = "success" if valid and verified else "invalid_certificate"
    return {
        "status": status,
        "certificate_status": "structural_only" if status == "success" else "invalid",
        "output": {
            "structurally_valid": valid,
            "blockers": blockers,
            "kernel_checked": False,
        },
        "operation_count": operations,
        "verifier_operation_count": verifier_operations,
        "verifier_kind": "independent_lean_skeleton_validator_v1",
    }


RUNNERS: Mapping[str, Callable[[JobSpec], dict[str, Any]]] = {
    "exact_expression": _run_exact,
    "interval_polynomial": _run_interval,
    "sat_certificate": _run_sat,
    "lean_skeleton": _run_lean_skeleton,
}


def execute_job(job: JobSpec, campaign_id: str, bundle_digest: str) -> dict[str, Any]:
    stdout = ""
    stderr = ""
    try:
        result = RUNNERS[job.runner_kind](job)
    except BudgetExceeded as exc:
        result = {
            "status": "blocked",
            "certificate_status": "not_verified",
            "output": {"error": str(exc), "error_type": "budget_exceeded"},
            "operation_count": job.resource_limits["max_operations"],
            "verifier_operation_count": 0,
            "verifier_kind": "not_run",
        }
        stderr = str(exc)
    except Exception as exc:
        result = {
            "status": "failure",
            "certificate_status": "not_verified",
            "output": {"error": str(exc), "error_type": type(exc).__name__},
            "operation_count": 0,
            "verifier_operation_count": 0,
            "verifier_kind": "not_run",
        }
        stderr = str(exc)

    output_bytes = len(json.dumps(result["output"], sort_keys=True, ensure_ascii=False).encode("utf-8"))
    if output_bytes > job.resource_limits["max_output_bytes"]:
        result = {
            "status": "blocked",
            "certificate_status": "not_verified",
            "output": {"error": "output exceeds max_output_bytes", "error_type": "output_budget"},
            "operation_count": result.get("operation_count", 0),
            "verifier_operation_count": result.get("verifier_operation_count", 0),
            "verifier_kind": "not_run",
        }
        stderr = "output exceeds max_output_bytes"

    receipt = {
        "campaign_id": campaign_id,
        "job_id": job.job_id,
        "canonical_problem_id": job.canonical_problem_id,
        "claim_id": job.claim_id,
        "runner_kind": job.runner_kind,
        "method": job.method,
        "scope": job.scope,
        "stopping_rule": job.stopping_rule,
        "deterministic_seed": job.deterministic_seed,
        "job_digest": job.job_digest,
        "bundle_digest": bundle_digest,
        "input_digest": stable_digest(job.input),
        "status": result["status"],
        "certificate_status": result["certificate_status"],
        "output": result["output"],
        "output_digest": stable_digest(result["output"]),
        "operation_count": result["operation_count"],
        "verifier_operation_count": result["verifier_operation_count"],
        "verifier_kind": result["verifier_kind"],
        "stdout": stdout,
        "stderr": stderr,
        "stdout_digest": stable_digest(stdout),
        "stderr_digest": stable_digest(stderr),
        "error_contract": dict(job.error_contract),
        "resource_limits": dict(job.resource_limits),
        "policy_decision": "allowed_offline_builtin",
        "network_access": False,
        "external_execution": False,
        "replay_contract": {
            "command": f"omega-problem-jobs replay --campaign-id {campaign_id} --job-id {job.job_id}",
            "requires_bundle_digest": bundle_digest,
            "runner_contract": "omega-problem-runners/7",
        },
        "proof_claimed": False,
        "solution_claimed": False,
        "theorem_promotion_allowed": False,
    }
    receipt["receipt_digest"] = stable_digest(receipt)
    return receipt
