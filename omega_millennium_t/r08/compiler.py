from __future__ import annotations

from dataclasses import asdict
import json
from pathlib import Path
from typing import Any, Mapping, Sequence

from .model import (
    EVENT_RULES,
    GENESIS_HASH,
    MANIFEST_SCHEMA,
    REPORT_SCHEMA,
    RoutingCell,
    RoutingEvent,
    file_receipt,
    load_cells,
    load_event_bundle,
    stable_digest,
    write_jsonl,
)


def build_ledger(
    ledger_id: str,
    raw_events: Sequence[Mapping[str, Any]],
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    previous = GENESIS_HASH
    for raw in raw_events:
        rule = EVENT_RULES[str(raw["event_type"])]
        base = {
            **dict(raw),
            "ledger_id": ledger_id,
            "previous_event_hash": previous,
            "routing_delta": int(rule["delta"]),
            "category": str(rule["category"]),
            "truth_probability_delta": None,
            "mathematical_truth_probability_claimed": False,
        }
        event_hash = stable_digest(base)
        event = RoutingEvent(
            event_id=str(base["event_id"]),
            sequence=int(base["sequence"]),
            occurred_at=str(base["occurred_at"]),
            cell_id=str(base["cell_id"]),
            event_type=str(base["event_type"]),
            evidence_ref=str(base["evidence_ref"]),
            observation=str(base["observation"]),
            source_digest=str(base["source_digest"]),
            previous_event_hash=previous,
            routing_delta=int(rule["delta"]),
            category=str(rule["category"]),
            event_hash=event_hash,
        )
        row = asdict(event)
        row["ledger_id"] = ledger_id
        row["truth_probability_delta"] = None
        row["mathematical_truth_probability_claimed"] = False
        rows.append(row)
        previous = event_hash
    return rows


def build_states(
    cells: Sequence[RoutingCell],
    ledger: Sequence[Mapping[str, Any]],
) -> list[dict[str, Any]]:
    events_by_cell: dict[str, list[Mapping[str, Any]]] = {cell.cell_id: [] for cell in cells}
    for event in ledger:
        events_by_cell[str(event["cell_id"])].append(event)
    rows: list[dict[str, Any]] = []
    for cell in cells:
        events = events_by_cell[cell.cell_id]
        total_delta = sum(int(event["routing_delta"]) for event in events)
        raw_score = cell.initial_routing_score + total_delta
        routing_score = min(100, max(0, raw_score))
        event_deltas = [
            {
                "event_id": event["event_id"],
                "event_type": event["event_type"],
                "delta": event["routing_delta"],
                "evidence_ref": event["evidence_ref"],
                "source_digest": event["source_digest"],
            }
            for event in events
        ]
        row = {
            "cell_id": cell.cell_id,
            "problem_id": cell.problem_id,
            "front": cell.front,
            "title": cell.title,
            "method_family": cell.method_family,
            "active": cell.active,
            "initial_routing_score": cell.initial_routing_score,
            "total_routing_delta": total_delta,
            "unclamped_routing_score": raw_score,
            "routing_score": routing_score,
            "event_count": len(events),
            "event_deltas": event_deltas,
            "latest_event_id": events[-1]["event_id"] if events else None,
            "latest_event_type": events[-1]["event_type"] if events else None,
            "routing_score_is_truth_probability": False,
            "mathematical_truth_probability_claimed": False,
        }
        row["state_digest"] = stable_digest(row)
        rows.append(row)
    rows.sort(key=lambda row: row["cell_id"])
    return rows


def select_diverse_portfolio(
    states: Sequence[Mapping[str, Any]],
    *,
    budget: int,
    max_per_problem: int,
) -> dict[str, Any]:
    if not isinstance(budget, int) or isinstance(budget, bool) or budget < 0:
        raise ValueError("budget must be a nonnegative integer")
    if not isinstance(max_per_problem, int) or isinstance(max_per_problem, bool) or max_per_problem < 1:
        raise ValueError("max_per_problem must be a positive integer")
    eligible = [row for row in states if row.get("active") is True]
    by_front: dict[str, list[Mapping[str, Any]]] = {}
    for row in eligible:
        by_front.setdefault(str(row["front"]), []).append(row)
    for rows in by_front.values():
        rows.sort(
            key=lambda row: (
                -int(row["routing_score"]),
                -int(row["total_routing_delta"]),
                str(row["problem_id"]),
                str(row["cell_id"]),
            )
        )
    fronts = sorted(by_front)
    positions = {front: 0 for front in fronts}
    problem_counts: dict[str, int] = {}
    selected: list[dict[str, Any]] = []
    selected_ids: set[str] = set()
    progress = True
    while len(selected) < min(budget, len(eligible)) and progress:
        progress = False
        for front in fronts:
            rows = by_front[front]
            while positions[front] < len(rows):
                candidate = rows[positions[front]]
                positions[front] += 1
                problem_id = str(candidate["problem_id"])
                if problem_counts.get(problem_id, 0) >= max_per_problem:
                    continue
                selected_ids.add(str(candidate["cell_id"]))
                problem_counts[problem_id] = problem_counts.get(problem_id, 0) + 1
                selected.append({
                    "rank": len(selected) + 1,
                    "cell_id": candidate["cell_id"],
                    "problem_id": problem_id,
                    "front": front,
                    "routing_score": candidate["routing_score"],
                    "total_routing_delta": candidate["total_routing_delta"],
                    "selection_basis": "diversity_round_robin_then_routing_score",
                })
                progress = True
                break
            if len(selected) >= budget:
                break
    return {
        "budget": budget,
        "max_per_problem": max_per_problem,
        "selected": selected,
        "selected_cell_ids": sorted(selected_ids),
        "selected_count": len(selected),
        "front_coverage": len({row["front"] for row in selected}),
        "problem_coverage": len({row["problem_id"] for row in selected}),
        "selection_is_truth_probability_ranking": False,
        "permanent_total_cap": None,
    }


def build_counterfactuals(
    cells: Sequence[RoutingCell],
    ledger: Sequence[Mapping[str, Any]],
    portfolio: Mapping[str, Any],
    *,
    budget: int,
    max_per_problem: int,
) -> list[dict[str, Any]]:
    selected_now = set(portfolio["selected_cell_ids"])
    by_cell: dict[str, list[Mapping[str, Any]]] = {cell.cell_id: [] for cell in cells}
    for event in ledger:
        by_cell[str(event["cell_id"])].append(event)
    rows: list[dict[str, Any]] = []
    for cell in cells:
        events = by_cell[cell.cell_id]
        if not events:
            row = {
                "cell_id": cell.cell_id,
                "selected_now": cell.cell_id in selected_now,
                "latest_event_id": None,
                "latest_event_type": None,
                "latest_event_delta": 0,
                "selected_without_latest_event": cell.cell_id in selected_now,
                "selection_changed_by_latest_event": False,
                "explanation": "No evidence event changed this cell from its initial routing state.",
            }
        else:
            reduced_ledger = [event for event in ledger if event["event_id"] != events[-1]["event_id"]]
            reduced_states = build_states(cells, reduced_ledger)
            reduced_portfolio = select_diverse_portfolio(
                reduced_states,
                budget=budget,
                max_per_problem=max_per_problem,
            )
            selected_without = cell.cell_id in set(reduced_portfolio["selected_cell_ids"])
            selected = cell.cell_id in selected_now
            latest = events[-1]
            direction = "entered" if selected and not selected_without else "left" if selected_without and not selected else "remained"
            row = {
                "cell_id": cell.cell_id,
                "selected_now": selected,
                "latest_event_id": latest["event_id"],
                "latest_event_type": latest["event_type"],
                "latest_event_delta": latest["routing_delta"],
                "selected_without_latest_event": selected_without,
                "selection_changed_by_latest_event": selected != selected_without,
                "explanation": (
                    f"The cell {direction} relative to the active portfolio when the latest "
                    f"evidence event ({latest['event_type']}, delta {latest['routing_delta']}) is removed."
                ),
            }
        row["counterfactual_digest"] = stable_digest(row)
        rows.append(row)
    rows.sort(key=lambda row: row["cell_id"])
    return rows


def build_mminus(ledger: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for event in ledger:
        rule = EVENT_RULES[str(event["event_type"])]
        if not bool(rule["mminus"]):
            continue
        row = {
            "mminus_id": f"mminus::routing::{event['event_id']}",
            "event_id": event["event_id"],
            "event_hash": event["event_hash"],
            "cell_id": event["cell_id"],
            "event_type": event["event_type"],
            "category": event["category"],
            "routing_delta": event["routing_delta"],
            "evidence_ref": event["evidence_ref"],
            "source_digest": event["source_digest"],
            "immutable": True,
        }
        row["mminus_digest"] = stable_digest(row)
        rows.append(row)
    return rows


def compile_routing_campaign(
    cells_jsonl: str | Path,
    events_json: str | Path,
    output_dir: str | Path,
    *,
    budget: int = 24,
    max_per_problem: int = 2,
) -> dict[str, Any]:
    cells = load_cells(cells_jsonl)
    ledger_id, raw_events = load_event_bundle(events_json, {cell.cell_id for cell in cells})
    ledger = build_ledger(ledger_id, raw_events)
    states = build_states(cells, ledger)
    portfolio = select_diverse_portfolio(states, budget=budget, max_per_problem=max_per_problem)
    counterfactuals = build_counterfactuals(
        cells,
        ledger,
        portfolio,
        budget=budget,
        max_per_problem=max_per_problem,
    )
    mminus = build_mminus(ledger)
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)

    cell_rows = [asdict(cell) for cell in cells]
    write_jsonl(output / "routing_cells.jsonl", cell_rows)
    write_jsonl(output / "event_ledger.jsonl", ledger)
    write_jsonl(output / "cell_states.jsonl", states)
    write_jsonl(output / "counterfactuals.jsonl", counterfactuals)
    write_jsonl(output / "mminus_records.jsonl", mminus)
    (output / "portfolio.json").write_text(
        json.dumps(portfolio, indent=2, sort_keys=True, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )

    artifact_names = (
        "routing_cells.jsonl",
        "event_ledger.jsonl",
        "cell_states.jsonl",
        "portfolio.json",
        "counterfactuals.jsonl",
        "mminus_records.jsonl",
    )
    manifest = {
        "schema": MANIFEST_SCHEMA,
        "ledger_id": ledger_id,
        "genesis_hash": GENESIS_HASH,
        "final_event_hash": ledger[-1]["event_hash"] if ledger else GENESIS_HASH,
        "event_rule_digest": stable_digest(EVENT_RULES),
        "artifacts": [file_receipt(output / name) for name in artifact_names],
        "event_deltas_user_supplied": False,
        "routing_score_is_truth_probability": False,
        "mminus_mutable": False,
        "permanent_total_cap": None,
        "proof_claimed": False,
        "solution_claimed": False,
    }
    manifest["digest"] = stable_digest({key: value for key, value in manifest.items() if key != "digest"})
    (output / "manifest.json").write_text(
        json.dumps(manifest, indent=2, sort_keys=True, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )

    report = {
        "schema": REPORT_SCHEMA,
        "status": "CERTIFIED_EVIDENCE_ROUTING_FIXTURE_R0_8",
        "ledger_id": ledger_id,
        "cell_count": len(cells),
        "event_count": len(ledger),
        "front_count": len({cell.front for cell in cells}),
        "problem_count": len({cell.problem_id for cell in cells}),
        "selected_count": portfolio["selected_count"],
        "front_coverage": portfolio["front_coverage"],
        "problem_coverage": portfolio["problem_coverage"],
        "mminus_record_count": len(mminus),
        "counterfactual_count": len(counterfactuals),
        "selection_change_count": sum(row["selection_changed_by_latest_event"] for row in counterfactuals),
        "event_rule_count": len(EVENT_RULES),
        "final_event_hash": manifest["final_event_hash"],
        "event_rule_digest": manifest["event_rule_digest"],
        "routing_score_is_truth_probability": False,
        "mathematical_truth_probability_claimed": False,
        "proof_claimed": False,
        "solution_claimed": False,
        "scientific_validation_claimed": False,
        "permanent_total_cap": None,
        "manifest_digest": manifest["digest"],
    }
    report["digest"] = stable_digest({key: value for key, value in report.items() if key != "digest"})
    (output / "report.json").write_text(
        json.dumps(report, indent=2, sort_keys=True, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    return report
