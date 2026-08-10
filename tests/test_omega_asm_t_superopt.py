from __future__ import annotations

import json

import pytest

from omega_asm_t.cli import main
from omega_asm_t.superopt import (
    certify_rewrite,
    enumerate_rewrites,
    expression_cost,
    one_step_rewrites,
    superoptimize,
)


def v(name: str):
    return {"op": "var", "name": name}


def c(value: int):
    return {"op": "const", "value": value}


def b(op: str, left, right):
    return {"op": op, "args": [left, right]}


def test_structural_cost_is_explicitly_not_cycles():
    expr = b("mul", v("x"), c(2))
    assert expression_cost(expr, 8) == 3.0
    assert expression_cost(b("shl", v("x"), c(1)), 8) == 1.0


def test_mul_power_of_two_generates_shift_candidate():
    rows = one_step_rewrites(b("mul", v("x"), c(8)), 8)
    assert any(rule == "mul-right-power2-to-shift" and candidate == b("shl", v("x"), c(3)) for rule, candidate in rows)


def test_add_zero_generates_identity_candidate():
    rows = one_step_rewrites(b("add", v("x"), c(0)), 8)
    assert any(candidate == v("x") for _, candidate in rows)


def test_add_self_generates_shift_candidate():
    rows = one_step_rewrites(b("add", v("x"), v("x")), 8)
    assert any(rule == "add-self-to-shift" and candidate == b("shl", v("x"), c(1)) for rule, candidate in rows)


def test_constant_folding_respects_modulo_width():
    rows = one_step_rewrites(b("add", c(15), c(2)), 4)
    assert any(candidate == c(1) for _, candidate in rows)


def test_rewrite_enumeration_is_bounded_and_deduplicated():
    rows = enumerate_rewrites(b("mul", b("add", v("x"), c(0)), c(2)), 8, max_candidates=12)
    assert len(rows) <= 12
    keys = [json.dumps(row["expression"], sort_keys=True) for row in rows]
    assert len(keys) == len(set(keys))


def test_false_rewrite_is_refuted_by_p7():
    proof = certify_rewrite(b("add", v("x"), v("y")), b("xor", v("x"), v("y")), 4)
    assert proof["accepted_equivalent"] is False
    assert proof["verification_status"] == "refuted_exhaustive"
    assert proof["counterexample"] is not None


def test_mul2_superoptimization_selects_shift_after_complete_proof():
    report = superoptimize({
        "name": "mul2",
        "width": 8,
        "expression": b("mul", v("x"), c(2)),
    })
    assert report["evidence_level"] == "bounded-proof-first-superoptimization"
    assert report["cost_model"]["calibrated"] is False
    assert report["cost_model"]["runtime_cycles"] is False
    assert report["original"]["structural_cost_units"] == 3.0
    assert report["best"]["expression"] == b("shl", v("x"), c(1))
    assert report["best"]["structural_cost_units"] == 1.0
    assert report["best"]["proof"]["accepted_equivalent"] is True
    assert report["improved_structural_cost"] is True
    assert report["selection_contract"]["unverified_candidate_can_win"] is False


def test_add_zero_superoptimization_selects_variable():
    report = superoptimize({
        "name": "add-zero",
        "width": 8,
        "expression": b("add", v("x"), c(0)),
    })
    assert report["best"]["expression"] == v("x")
    assert report["best"]["structural_cost_units"] == 0.0


def test_large_domain_prevents_unproven_candidate_from_winning():
    report = superoptimize({
        "name": "large-domain",
        "width": 16,
        "expression": b("add", b("add", v("x"), c(0)), v("y")),
    }, max_states=1000)
    assert report["best"]["expression"] == report["original"]["expression"]
    non_reflexive = [row for row in report["candidates"] if row["proof"]["verification_status"] != "reflexive_baseline"]
    assert non_reflexive
    assert all(row["proof"]["accepted_equivalent"] is False for row in non_reflexive)


def test_candidate_bound_validation():
    with pytest.raises(ValueError, match="positive integer"):
        enumerate_rewrites(v("x"), 8, max_candidates=0)


def test_cli_superopt(tmp_path, capsys):
    spec = {
        "name": "cli-mul2",
        "width": 8,
        "expression": b("mul", v("x"), c(2)),
    }
    path = tmp_path / "spec.json"
    path.write_text(json.dumps(spec), encoding="utf-8")
    assert main(["superopt", str(path), "--max-candidates", "32", "--max-states", "1000000"]) == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["best"]["expression"] == b("shl", v("x"), c(1))
    assert payload["best"]["proof"]["accepted_equivalent"] is True
