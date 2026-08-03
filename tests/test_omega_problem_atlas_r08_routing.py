from __future__ import annotations

import json
from pathlib import Path

import pytest

from omega_millennium_t.r08 import EVENT_RULES, audit_routing_campaign, compile_routing_campaign


def _cell(
    cell_id: str,
    problem_id: str,
    front: str,
    score: int,
    *,
    active: bool = True,
) -> dict:
    return {
        "cell_id": cell_id,
        "problem_id": problem_id,
        "front": front,
        "title": f"Research cell {cell_id}",
        "initial_routing_score": score,
        "method_family": "fixture_method",
        "active": active,
        "provenance_refs": [f"fixture:{cell_id}"],
    }


def _write_cells(path: Path) -> Path:
    rows = [
        _cell("cell.a1", "problem.a", "front_alpha", 40),
        _cell("cell.a2", "problem.a2", "front_alpha", 55),
        _cell("cell.b1", "problem.b", "front_beta", 45),
        _cell("cell.b2", "problem.b2", "front_beta", 50),
        _cell("cell.c1", "problem.c", "front_gamma", 35),
        _cell("cell.c2", "problem.c2", "front_gamma", 60),
    ]
    path.write_text(
        "".join(json.dumps(row, sort_keys=True) + "\n" for row in rows),
        encoding="utf-8",
    )
    return path


def _event(
    sequence: int,
    cell_id: str,
    event_type: str,
    *,
    occurred_at: str | None = None,
) -> dict:
    return {
        "event_id": f"event.{sequence:03d}",
        "sequence": sequence,
        "occurred_at": occurred_at or f"2026-08-03T16:{sequence:02d}:00Z",
        "cell_id": cell_id,
        "event_type": event_type,
        "evidence_ref": f"fixture:evidence:{sequence}",
        "observation": f"Observed {event_type} for {cell_id}",
        "source_digest": f"{sequence % 10}" * 64,
    }


def _write_events(path: Path, events: list[dict]) -> Path:
    path.write_text(
        json.dumps(
            {
                "schema": "omega-problem-routing-events/8",
                "ledger_id": "ledger-fixture-r08",
                "events": events,
            },
            indent=2,
            sort_keys=True,
        ),
        encoding="utf-8",
    )
    return path


def _read_jsonl(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line]


def test_fixed_deltas_hash_chain_and_diverse_selection(tmp_path: Path) -> None:
    cells = _write_cells(tmp_path / "cells.jsonl")
    events = _write_events(tmp_path / "events.json", [
        _event(1, "cell.a1", "bound_improved"),
        _event(2, "cell.b1", "known_case_reproduced"),
        _event(3, "cell.c1", "formal_artifact_kernel_checked"),
    ])
    output = tmp_path / "output"
    report = compile_routing_campaign(cells, events, output, budget=3, max_per_problem=1)
    ledger = _read_jsonl(output / "event_ledger.jsonl")
    states = {row["cell_id"]: row for row in _read_jsonl(output / "cell_states.jsonl")}
    portfolio = json.loads((output / "portfolio.json").read_text(encoding="utf-8"))

    assert report["cell_count"] == 6
    assert report["event_count"] == 3
    assert ledger[0]["previous_event_hash"] == "0" * 64
    assert ledger[1]["previous_event_hash"] == ledger[0]["event_hash"]
    assert ledger[2]["previous_event_hash"] == ledger[1]["event_hash"]
    assert ledger[0]["routing_delta"] == EVENT_RULES["bound_improved"]["delta"]
    assert ledger[2]["routing_delta"] == EVENT_RULES["formal_artifact_kernel_checked"]["delta"]
    assert all(row["truth_probability_delta"] is None for row in ledger)
    assert states["cell.a1"]["routing_score"] == 60
    assert states["cell.b1"]["routing_score"] == 57
    assert states["cell.c1"]["routing_score"] == 60
    assert portfolio["selected_count"] == 3
    assert portfolio["front_coverage"] == 3
    assert {row["front"] for row in portfolio["selected"]} == {
        "front_alpha", "front_beta", "front_gamma"
    }
    assert portfolio["selection_is_truth_probability_ranking"] is False
    assert audit_routing_campaign(output)["valid"] is True


def test_repeated_failures_lower_priority_and_preserve_mminus(tmp_path: Path) -> None:
    cells = _write_cells(tmp_path / "cells.jsonl")
    events = _write_events(tmp_path / "events.json", [
        _event(1, "cell.a2", "method_timeout"),
        _event(2, "cell.a2", "method_diverged"),
        _event(3, "cell.a2", "duplicate_known_work"),
    ])
    output = tmp_path / "output"
    report = compile_routing_campaign(cells, events, output, budget=3, max_per_problem=1)
    state = next(
        row for row in _read_jsonl(output / "cell_states.jsonl")
        if row["cell_id"] == "cell.a2"
    )
    mminus = _read_jsonl(output / "mminus_records.jsonl")

    expected_delta = sum(
        EVENT_RULES[name]["delta"]
        for name in ("method_timeout", "method_diverged", "duplicate_known_work")
    )
    assert state["total_routing_delta"] == expected_delta
    assert state["routing_score"] == max(0, 55 + expected_delta)
    assert report["mminus_record_count"] == 3
    assert {row["event_type"] for row in mminus} == {
        "method_timeout", "method_diverged", "duplicate_known_work"
    }
    assert all(row["immutable"] is True for row in mminus)


def test_latest_event_counterfactual_explains_portfolio_entry(tmp_path: Path) -> None:
    cells = _write_cells(tmp_path / "cells.jsonl")
    events = _write_events(tmp_path / "events.json", [
        _event(1, "cell.a1", "formal_artifact_kernel_checked"),
    ])
    output = tmp_path / "output"
    compile_routing_campaign(cells, events, output, budget=3, max_per_problem=1)
    counterfactual = next(
        row for row in _read_jsonl(output / "counterfactuals.jsonl")
        if row["cell_id"] == "cell.a1"
    )

    assert counterfactual["selected_now"] is True
    assert counterfactual["selected_without_latest_event"] is False
    assert counterfactual["selection_changed_by_latest_event"] is True
    assert "entered" in counterfactual["explanation"]


def test_materialization_is_deterministic(tmp_path: Path) -> None:
    cells = _write_cells(tmp_path / "cells.jsonl")
    events = _write_events(tmp_path / "events.json", [
        _event(1, "cell.a1", "source_status_verified"),
        _event(2, "cell.b2", "computation_invalid_certificate"),
        _event(3, "cell.c2", "independent_review_accepted"),
    ])
    first, second = tmp_path / "first", tmp_path / "second"
    report_a = compile_routing_campaign(cells, events, first, budget=4, max_per_problem=1)
    report_b = compile_routing_campaign(cells, events, second, budget=4, max_per_problem=1)

    assert report_a == report_b
    left = sorted(path.name for path in first.iterdir() if path.is_file())
    right = sorted(path.name for path in second.iterdir() if path.is_file())
    assert left == right
    for name in left:
        assert (first / name).read_bytes() == (second / name).read_bytes(), name


def test_user_cannot_supply_delta_hash_or_truth_probability(tmp_path: Path) -> None:
    cells = _write_cells(tmp_path / "cells.jsonl")
    event = _event(1, "cell.a1", "bound_improved")
    event["routing_delta"] = 999
    events = _write_events(tmp_path / "events.json", [event])
    with pytest.raises(ValueError, match="compiler-owned"):
        compile_routing_campaign(cells, events, tmp_path / "output")

    event = _event(1, "cell.a1", "bound_improved")
    event["truth_probability_delta"] = 0.9
    events = _write_events(tmp_path / "truth.json", [event])
    with pytest.raises(ValueError, match="compiler-owned"):
        compile_routing_campaign(cells, events, tmp_path / "output-two")


def test_sequences_and_timestamps_fail_closed(tmp_path: Path) -> None:
    cells = _write_cells(tmp_path / "cells.jsonl")
    bad_sequence = _event(2, "cell.a1", "bound_improved")
    events = _write_events(tmp_path / "bad-sequence.json", [bad_sequence])
    with pytest.raises(ValueError, match="sequence must be contiguous"):
        compile_routing_campaign(cells, events, tmp_path / "output")

    events = _write_events(tmp_path / "bad-time.json", [
        _event(1, "cell.a1", "bound_improved", occurred_at="2026-08-03T17:00:00Z"),
        _event(2, "cell.b1", "known_case_reproduced", occurred_at="2026-08-03T16:00:00Z"),
    ])
    with pytest.raises(ValueError, match="timestamps must be nondecreasing"):
        compile_routing_campaign(cells, events, tmp_path / "output-two")


def test_audit_detects_event_and_portfolio_tampering(tmp_path: Path) -> None:
    cells = _write_cells(tmp_path / "cells.jsonl")
    events = _write_events(tmp_path / "events.json", [
        _event(1, "cell.a1", "bound_improved"),
        _event(2, "cell.b1", "method_timeout"),
    ])
    output = tmp_path / "output"
    compile_routing_campaign(cells, events, output, budget=3, max_per_problem=1)

    ledger_path = output / "event_ledger.jsonl"
    rows = ledger_path.read_text(encoding="utf-8").splitlines()
    payload = json.loads(rows[0])
    payload["routing_delta"] = 999
    rows[0] = json.dumps(payload, sort_keys=True)
    ledger_path.write_text("\n".join(rows) + "\n", encoding="utf-8")
    audit = audit_routing_campaign(output)
    assert audit["valid"] is False
    assert any(
        "event_ledger.jsonl: sha256 mismatch" in error
        or "routing delta differs" in error
        for error in audit["errors"]
    )
