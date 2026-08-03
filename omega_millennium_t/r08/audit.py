from __future__ import annotations

from dataclasses import asdict
import json
from pathlib import Path
from typing import Any

from .compiler import (
    build_counterfactuals,
    build_mminus,
    build_states,
    select_diverse_portfolio,
)
from .model import (
    EVENT_RULES,
    GENESIS_HASH,
    RoutingCell,
    file_receipt,
    read_jsonl,
    stable_digest,
)


def audit_routing_campaign(output_dir: str | Path) -> dict[str, Any]:
    output = Path(output_dir)
    required = {
        "routing_cells.jsonl",
        "event_ledger.jsonl",
        "cell_states.jsonl",
        "portfolio.json",
        "counterfactuals.jsonl",
        "mminus_records.jsonl",
        "manifest.json",
        "report.json",
    }
    missing = sorted(name for name in required if not (output / name).exists())
    if missing:
        return {
            "schema": "omega-problem-routing-audit/8",
            "valid": False,
            "errors": [f"missing artifact: {name}" for name in missing],
            "solution_claimed": False,
        }

    errors: list[str] = []
    manifest = json.loads((output / "manifest.json").read_text(encoding="utf-8"))
    report = json.loads((output / "report.json").read_text(encoding="utf-8"))
    portfolio = json.loads((output / "portfolio.json").read_text(encoding="utf-8"))
    if manifest.get("digest") != stable_digest({k: v for k, v in manifest.items() if k != "digest"}):
        errors.append("manifest digest mismatch")
    if report.get("digest") != stable_digest({k: v for k, v in report.items() if k != "digest"}):
        errors.append("report digest mismatch")

    manifest_artifacts = {item["path"]: item for item in manifest.get("artifacts", [])}
    for name in required - {"manifest.json", "report.json"}:
        expected = manifest_artifacts.get(name)
        if expected is None:
            errors.append(f"manifest missing {name}")
            continue
        actual = file_receipt(output / name)
        for field in ("sha256", "bytes", "rows"):
            if actual[field] != expected.get(field):
                errors.append(f"{name}: {field} mismatch")

    cell_rows = read_jsonl(output / "routing_cells.jsonl")
    ledger = read_jsonl(output / "event_ledger.jsonl")
    states = read_jsonl(output / "cell_states.jsonl")
    counterfactuals = read_jsonl(output / "counterfactuals.jsonl")
    mminus = read_jsonl(output / "mminus_records.jsonl")

    cells: list[RoutingCell] = []
    for row in cell_rows:
        expected = stable_digest({k: v for k, v in row.items() if k != "cell_digest"})
        if row.get("cell_digest") != expected:
            errors.append(f"{row.get('cell_id')}: cell digest mismatch")
        try:
            cells.append(RoutingCell(**row))
        except TypeError as exc:
            errors.append(f"{row.get('cell_id')}: invalid cell shape: {exc}")
    cells.sort(key=lambda cell: cell.cell_id)
    if len({cell.cell_id for cell in cells}) != len(cells):
        errors.append("duplicate cell_id")
    known_cells = {cell.cell_id for cell in cells}

    previous = GENESIS_HASH
    seen_events: set[str] = set()
    for expected_sequence, event in enumerate(ledger, 1):
        event_id = str(event.get("event_id", ""))
        if event_id in seen_events:
            errors.append(f"{event_id}: duplicate event")
        seen_events.add(event_id)
        if event.get("sequence") != expected_sequence:
            errors.append(f"{event_id}: non-contiguous sequence")
        if event.get("cell_id") not in known_cells:
            errors.append(f"{event_id}: unknown cell")
        event_type = str(event.get("event_type", ""))
        rule = EVENT_RULES.get(event_type)
        if rule is None:
            errors.append(f"{event_id}: unknown event type")
            continue
        if event.get("routing_delta") != rule["delta"]:
            errors.append(f"{event_id}: routing delta differs from fixed rule")
        if event.get("category") != rule["category"]:
            errors.append(f"{event_id}: event category differs from fixed rule")
        if event.get("previous_event_hash") != previous:
            errors.append(f"{event_id}: previous hash mismatch")
        base = {
            "event_id": event.get("event_id"),
            "sequence": event.get("sequence"),
            "occurred_at": event.get("occurred_at"),
            "cell_id": event.get("cell_id"),
            "event_type": event.get("event_type"),
            "evidence_ref": event.get("evidence_ref"),
            "observation": event.get("observation"),
            "source_digest": event.get("source_digest"),
            "ledger_id": event.get("ledger_id"),
            "previous_event_hash": event.get("previous_event_hash"),
            "routing_delta": event.get("routing_delta"),
            "category": event.get("category"),
            "truth_probability_delta": event.get("truth_probability_delta"),
            "mathematical_truth_probability_claimed": event.get("mathematical_truth_probability_claimed"),
        }
        expected_hash = stable_digest(base)
        if event.get("event_hash") != expected_hash:
            errors.append(f"{event_id}: event hash mismatch")
        if event.get("truth_probability_delta") is not None:
            errors.append(f"{event_id}: truth probability delta must be null")
        if event.get("mathematical_truth_probability_claimed") is not False:
            errors.append(f"{event_id}: mathematical truth probability claimed")
        previous = str(event.get("event_hash", ""))

    if manifest.get("genesis_hash") != GENESIS_HASH:
        errors.append("manifest genesis hash mismatch")
    if manifest.get("final_event_hash") != (previous if ledger else GENESIS_HASH):
        errors.append("manifest final event hash mismatch")
    if manifest.get("event_rule_digest") != stable_digest(EVENT_RULES):
        errors.append("event rule digest mismatch")

    recomputed_states = build_states(cells, ledger)
    if states != recomputed_states:
        errors.append("cell states do not match genesis replay")
    for row in states:
        expected = stable_digest({k: v for k, v in row.items() if k != "state_digest"})
        if row.get("state_digest") != expected:
            errors.append(f"{row.get('cell_id')}: state digest mismatch")
        if row.get("routing_score_is_truth_probability") is not False:
            errors.append(f"{row.get('cell_id')}: routing score mislabeled as truth probability")
        if row.get("mathematical_truth_probability_claimed") is not False:
            errors.append(f"{row.get('cell_id')}: mathematical truth probability claimed")

    budget = portfolio.get("budget")
    max_per_problem = portfolio.get("max_per_problem")
    try:
        recomputed_portfolio = select_diverse_portfolio(
            states,
            budget=int(budget),
            max_per_problem=int(max_per_problem),
        )
    except (TypeError, ValueError) as exc:
        errors.append(f"portfolio parameters invalid: {exc}")
        recomputed_portfolio = None
    if recomputed_portfolio is not None and portfolio != recomputed_portfolio:
        errors.append("portfolio does not match deterministic diversity selection")
    if portfolio.get("selection_is_truth_probability_ranking") is not False:
        errors.append("portfolio must not be a truth probability ranking")

    if recomputed_portfolio is not None:
        recomputed_counterfactuals = build_counterfactuals(
            cells,
            ledger,
            portfolio,
            budget=int(budget),
            max_per_problem=int(max_per_problem),
        )
        if counterfactuals != recomputed_counterfactuals:
            errors.append("counterfactual report does not match replay")
    for row in counterfactuals:
        expected = stable_digest({k: v for k, v in row.items() if k != "counterfactual_digest"})
        if row.get("counterfactual_digest") != expected:
            errors.append(f"{row.get('cell_id')}: counterfactual digest mismatch")

    recomputed_mminus = build_mminus(ledger)
    if mminus != recomputed_mminus:
        errors.append("M-minus records do not match event ledger")
    for row in mminus:
        expected = stable_digest({k: v for k, v in row.items() if k != "mminus_digest"})
        if row.get("mminus_digest") != expected:
            errors.append(f"{row.get('mminus_id')}: M-minus digest mismatch")
        if row.get("immutable") is not True:
            errors.append(f"{row.get('mminus_id')}: M-minus must be immutable")

    expected_counts = {
        "cell_count": len(cells),
        "event_count": len(ledger),
        "front_count": len({cell.front for cell in cells}),
        "problem_count": len({cell.problem_id for cell in cells}),
        "selected_count": portfolio.get("selected_count"),
        "front_coverage": portfolio.get("front_coverage"),
        "problem_coverage": portfolio.get("problem_coverage"),
        "mminus_record_count": len(mminus),
        "counterfactual_count": len(counterfactuals),
        "selection_change_count": sum(bool(row.get("selection_changed_by_latest_event")) for row in counterfactuals),
        "event_rule_count": len(EVENT_RULES),
        "final_event_hash": manifest.get("final_event_hash"),
        "event_rule_digest": manifest.get("event_rule_digest"),
        "manifest_digest": manifest.get("digest"),
    }
    for field, expected in expected_counts.items():
        if report.get(field) != expected:
            errors.append(f"report {field}: expected {expected!r}, got {report.get(field)!r}")

    if manifest.get("event_deltas_user_supplied") is not False:
        errors.append("event deltas must not be user supplied")
    if manifest.get("routing_score_is_truth_probability") is not False:
        errors.append("manifest must distinguish routing score from truth probability")
    if manifest.get("mminus_mutable") is not False:
        errors.append("manifest must keep M-minus immutable")
    for field in (
        "routing_score_is_truth_probability",
        "mathematical_truth_probability_claimed",
        "proof_claimed",
        "solution_claimed",
        "scientific_validation_claimed",
    ):
        if report.get(field) is not False:
            errors.append(f"{field} must be false")
    if report.get("permanent_total_cap", "missing") is not None:
        errors.append("permanent_total_cap must be null")

    return {
        "schema": "omega-problem-routing-audit/8",
        "valid": not errors,
        "errors": errors,
        "cell_count": len(cells),
        "event_count": len(ledger),
        "selected_count": portfolio.get("selected_count"),
        "mminus_record_count": len(mminus),
        "final_event_hash": manifest.get("final_event_hash"),
        "manifest_digest": manifest.get("digest"),
        "report_digest": report.get("digest"),
        "solution_claimed": False,
    }
