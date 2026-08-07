from __future__ import annotations

import json

import pytest

from omega_asm_t.cli import main
from omega_asm_t.formal import (
    build_equivalence_obligation,
    build_p7_certificate,
    evaluate_expr,
    exhaustive_verify,
    normalize_equivalence_spec,
    normalize_expr,
    obligation_id,
    parse_solver_status,
)


def _var(name: str):
    return {"op": "var", "name": name}


def _const(value: int):
    return {"op": "const", "value": value}


def _bin(op: str, left, right):
    return {"op": op, "args": [left, right]}


def _commutativity_spec(width: int = 4):
    x = _var("x")
    y = _var("y")
    return {
        "name": "add-commutativity",
        "width": width,
        "lhs": _bin("add", x, y),
        "rhs": _bin("add", y, x),
    }


def test_normalization_masks_constants_to_width():
    assert normalize_expr(_const(-1), 4) == {"op": "const", "value": 15}
    assert normalize_expr(_const(17), 4) == {"op": "const", "value": 1}


def test_bad_variable_name_is_rejected():
    with pytest.raises(ValueError, match="variable name"):
        normalize_expr(_var("x;drop"), 8)


def test_unsupported_op_is_rejected():
    with pytest.raises(ValueError, match="unsupported"):
        normalize_expr({"op": "divide", "args": [_var("x"), _var("y")]}, 8)


def test_shift_semantics_match_fixed_width_bitvectors():
    expr = normalize_expr(_bin("shl", _var("x"), _var("s")), 4)
    assert evaluate_expr(expr, {"x": 3, "s": 1}, 4) == 6
    assert evaluate_expr(expr, {"x": 3, "s": 4}, 4) == 0


def test_obligation_is_deterministic_and_declares_qf_bv():
    left = build_equivalence_obligation(_commutativity_spec())
    right = build_equivalence_obligation(_commutativity_spec())
    assert left["obligation_id"] == right["obligation_id"] == obligation_id(_commutativity_spec())
    assert left["smt_logic"] == "QF_BV"
    assert "(declare-fun x () (_ BitVec 4))" in left["smt2"]
    assert "(declare-fun y () (_ BitVec 4))" in left["smt2"]
    assert "(assert (not (= " in left["smt2"]
    assert left["smt2"].rstrip().endswith("(check-sat)")


def test_exhaustive_verification_proves_add_commutativity_for_entire_domain():
    evidence = exhaustive_verify(_commutativity_spec(width=4))
    assert evidence["status"] == "equivalent"
    assert evidence["complete"] is True
    assert evidence["states_total"] == 256
    assert evidence["states_checked"] == 256


def test_exhaustive_verification_finds_counterexample_for_add_vs_xor():
    spec = {
        "name": "false-add-xor",
        "width": 4,
        "lhs": _bin("add", _var("x"), _var("y")),
        "rhs": _bin("xor", _var("x"), _var("y")),
    }
    evidence = exhaustive_verify(spec)
    assert evidence["status"] == "counterexample"
    assert evidence["complete"] is True
    assert evidence["counterexample"] is not None
    assert evidence["lhs_value"] != evidence["rhs_value"]


def test_exhaustive_verification_respects_state_budget():
    spec = {
        "name": "three-vars-large",
        "width": 8,
        "lhs": _bin("add", _bin("add", _var("x"), _var("y")), _var("z")),
        "rhs": _bin("add", _var("x"), _bin("add", _var("y"), _var("z"))),
    }
    evidence = exhaustive_verify(spec, max_states=1_000_000)
    assert evidence["status"] == "not_run"
    assert evidence["complete"] is False
    assert evidence["states_total"] == 256**3
    assert evidence["states_checked"] == 0


def test_mul_by_two_and_shift_left_are_equivalent_modulo_width():
    spec = {
        "name": "mul2-shl1",
        "width": 8,
        "lhs": _bin("mul", _var("x"), _const(2)),
        "rhs": _bin("shl", _var("x"), _const(1)),
    }
    evidence = exhaustive_verify(spec)
    assert evidence["status"] == "equivalent"
    assert evidence["states_checked"] == 256


def test_solver_status_parser_is_conservative():
    assert parse_solver_status("unsat\n") == "unsat"
    assert parse_solver_status("; comment\nSAT\n") == "sat"
    assert parse_solver_status("unknown\n") == "unknown"
    assert parse_solver_status("solver crashed\n") == "invalid"
    assert parse_solver_status(None) is None


def test_dual_evidence_accepts_only_bounded_statement_and_not_kernel_checked():
    certificate = build_p7_certificate(
        _commutativity_spec(),
        solver_text="unsat\n",
        solver_name="z3",
        solver_version="test",
    )
    assert certificate["verification_status"] == "dual_verified_bounded"
    assert certificate["accepted_equivalent"] is True
    assert certificate["kernel_checked"] is False
    assert certificate["claim_scope"] == "fixed_width_bitvector_semantics_only"
    assert certificate["solver_evidence"]["status"] == "unsat"
    assert certificate["solver_evidence"]["solver_text_alone_grants_acceptance"] is False


def test_exhaustive_only_can_accept_complete_bounded_domain():
    certificate = build_p7_certificate(_commutativity_spec(), solver_text=None)
    assert certificate["verification_status"] == "exhaustive_verified_bounded"
    assert certificate["accepted_equivalent"] is True


def test_solver_unsat_without_complete_exhaustive_check_is_observed_not_accepted():
    spec = {
        "name": "large-associativity",
        "width": 8,
        "lhs": _bin("add", _bin("add", _var("x"), _var("y")), _var("z")),
        "rhs": _bin("add", _var("x"), _bin("add", _var("y"), _var("z"))),
    }
    certificate = build_p7_certificate(spec, solver_text="unsat\n", max_states=1000)
    assert certificate["verification_status"] == "solver_unsat_observed"
    assert certificate["accepted_equivalent"] is False


def test_conflicting_solver_and_exhaustive_evidence_is_never_accepted():
    certificate = build_p7_certificate(_commutativity_spec(), solver_text="sat\n")
    assert certificate["verification_status"] == "evidence_conflict"
    assert certificate["accepted_equivalent"] is False


def test_refuted_expression_is_never_accepted():
    spec = {
        "name": "false",
        "width": 3,
        "lhs": _bin("add", _var("x"), _var("y")),
        "rhs": _bin("xor", _var("x"), _var("y")),
    }
    certificate = build_p7_certificate(spec)
    assert certificate["verification_status"] == "refuted_exhaustive"
    assert certificate["accepted_equivalent"] is False
    assert certificate["exhaustive_evidence"]["counterexample"] is not None


def test_normalized_spec_caps_variable_count_and_preserves_sorted_variables():
    spec = _commutativity_spec()
    normalized = normalize_equivalence_spec(spec)
    assert normalized["variables"] == ["x", "y"]


def test_cli_p7_obligation_and_certificate(tmp_path, capsys):
    spec_path = tmp_path / "spec.json"
    solver_path = tmp_path / "solver.txt"
    spec_path.write_text(json.dumps(_commutativity_spec()), encoding="utf-8")
    solver_path.write_text("unsat\n", encoding="utf-8")

    assert main(["p7-obligation", str(spec_path)]) == 0
    obligation = json.loads(capsys.readouterr().out)
    assert obligation["evidence_level"] == "P7-bounded-equivalence-obligation"

    assert main([
        "p7-certificate",
        str(spec_path),
        "--solver-result",
        str(solver_path),
        "--solver-name",
        "z3",
        "--solver-version",
        "test",
    ]) == 0
    certificate = json.loads(capsys.readouterr().out)
    assert certificate["verification_status"] == "dual_verified_bounded"
    assert certificate["accepted_equivalent"] is True
