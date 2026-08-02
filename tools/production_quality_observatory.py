#!/usr/bin/env python3
"""Ω-PRODUCTION-QUALITY-OBSERVATORY-T R0.1.

Evaluate repository production without conflating virtual scale, materialized
records, synthetic execution, external scientific evidence, product adoption,
or revenue. The evaluator is deterministic, dependency-free and read-only.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Mapping


class ObservatoryError(ValueError):
    """Raised when an observatory input violates a required invariant."""


def load_json(path: str | Path) -> dict[str, Any]:
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ObservatoryError(f"Expected a JSON object in {path}")
    return payload


def _require_mapping(parent: Mapping[str, Any], key: str) -> Mapping[str, Any]:
    value = parent.get(key)
    if not isinstance(value, Mapping):
        raise ObservatoryError(f"Missing or invalid mapping: {key}")
    return value


def _require_non_negative_number(parent: Mapping[str, Any], key: str) -> float:
    value = parent.get(key)
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ObservatoryError(f"Expected numeric value for {key}")
    if value < 0:
        raise ObservatoryError(f"Negative values are forbidden for {key}")
    return float(value)


def validate_snapshot(snapshot: Mapping[str, Any]) -> None:
    repository_state = _require_mapping(snapshot, "repository_state")
    volume_classes = _require_mapping(snapshot, "volume_classes")
    external = _require_mapping(snapshot, "external_evidence_observed_in_scope")

    for key in (
        "merged_pull_requests",
        "open_pull_requests",
        "merged_pr_commit_associations",
        "open_pr_commit_associations",
    ):
        _require_non_negative_number(repository_state, key)

    actual = _require_mapping(volume_classes, "actual_materialized_or_executed_minimum")
    _require_non_negative_number(actual, "value")

    virtual = _require_mapping(volume_classes, "largest_virtual_plan")
    _require_non_negative_number(virtual, "value")
    if virtual.get("materialized") is not False or virtual.get("executed") is not False:
        raise ObservatoryError(
            "largest_virtual_plan must explicitly remain non-materialized and non-executed"
        )

    for key in (
        "real_instrument_datasets_with_provenance",
        "independent_replications",
        "external_domain_expert_reviews",
        "external_active_users",
        "external_pilots",
        "confirmed_revenue_events",
        "peer_reviewed_publications",
    ):
        _require_non_negative_number(external, key)


def _threshold(policy: Mapping[str, Any], gate: str, field: str) -> float:
    gates = _require_mapping(policy, "gates")
    gate_payload = _require_mapping(gates, gate)
    green = _require_mapping(gate_payload, "green_when")
    return _require_non_negative_number(green, field)


def evaluate(
    snapshot: Mapping[str, Any], policy: Mapping[str, Any]
) -> dict[str, Any]:
    """Return a multi-gate evaluation with no sovereign scalar score."""

    validate_snapshot(snapshot)
    repository_state = _require_mapping(snapshot, "repository_state")
    volume_classes = _require_mapping(snapshot, "volume_classes")
    external = _require_mapping(snapshot, "external_evidence_observed_in_scope")

    actual = _require_mapping(volume_classes, "actual_materialized_or_executed_minimum")
    actual_value = _require_non_negative_number(actual, "value")
    virtual = _require_mapping(volume_classes, "largest_virtual_plan")
    virtual_value = _require_non_negative_number(virtual, "value")

    volume_minimum = _threshold(
        policy,
        "volume_gate",
        "actual_materialized_or_executed_minimum_gte",
    )
    volume_gate = actual_value >= volume_minimum
    virtual_separation = (
        virtual.get("materialized") is False and virtual.get("executed") is False
    )

    integration_gate = bool(
        repository_state.get("global_python_compile_observed_success")
        and repository_state.get("global_pytest_observed_success")
    )

    open_pr_limit = _threshold(policy, "wip_gate", "open_pull_requests_lte")
    open_commit_limit = _threshold(
        policy, "wip_gate", "open_pr_commit_associations_lte"
    )
    open_prs = _require_non_negative_number(repository_state, "open_pull_requests")
    open_commits = _require_non_negative_number(
        repository_state, "open_pr_commit_associations"
    )
    wip_gate = open_prs <= open_pr_limit and open_commits <= open_commit_limit

    science_signals = {
        "real_instrument_datasets_with_provenance": _require_non_negative_number(
            external, "real_instrument_datasets_with_provenance"
        ),
        "independent_replications": _require_non_negative_number(
            external, "independent_replications"
        ),
        "external_domain_expert_reviews": _require_non_negative_number(
            external, "external_domain_expert_reviews"
        ),
    }
    product_signals = {
        "external_active_users": _require_non_negative_number(
            external, "external_active_users"
        ),
        "external_pilots": _require_non_negative_number(external, "external_pilots"),
        "confirmed_revenue_events": _require_non_negative_number(
            external, "confirmed_revenue_events"
        ),
    }
    external_science_gate = any(value >= 1 for value in science_signals.values())
    external_product_gate = any(value >= 1 for value in product_signals.values())

    if not wip_gate:
        decision = "REDUCE_WIP_AND_EXTERNALIZE"
    elif not external_science_gate or not external_product_gate:
        decision = "CONSOLIDATE_AND_EXTERNALIZE"
    else:
        decision = "SELECTIVE_EXPANSION_ALLOWED"

    warnings: list[str] = []
    if virtual_value > actual_value:
        warnings.append(
            "Virtual address space exceeds actual execution and must remain excluded from actual-volume claims."
        )
    if not wip_gate:
        warnings.append(
            "Open-PR count or associated commit count exceeds the consolidation policy."
        )
    if not external_science_gate:
        warnings.append(
            "No external scientific evidence was confirmed inside the inspected scope."
        )
    if not external_product_gate:
        warnings.append(
            "No external user, pilot or revenue evidence was confirmed inside the inspected scope."
        )

    return {
        "observatory_version": "0.1.0",
        "snapshot_id": snapshot.get("snapshot_id"),
        "repository": snapshot.get("repository"),
        "decision": decision,
        "gates": {
            "volume": {
                "status": "GREEN" if volume_gate and virtual_separation else "RED",
                "actual_minimum": int(actual_value),
                "required_minimum": int(volume_minimum),
                "virtual_plan_excluded": virtual_separation,
                "largest_virtual_plan": int(virtual_value),
            },
            "integration": {
                "status": "GREEN" if integration_gate else "RED",
                "global_compile": bool(
                    repository_state.get("global_python_compile_observed_success")
                ),
                "global_pytest": bool(
                    repository_state.get("global_pytest_observed_success")
                ),
            },
            "wip": {
                "status": "GREEN" if wip_gate else "RED",
                "open_pull_requests": int(open_prs),
                "open_pull_request_limit": int(open_pr_limit),
                "open_pr_commit_associations": int(open_commits),
                "open_commit_limit": int(open_commit_limit),
            },
            "external_science": {
                "status": "GREEN" if external_science_gate else "RED",
                "signals": science_signals,
            },
            "external_product": {
                "status": "GREEN" if external_product_gate else "RED",
                "signals": product_signals,
            },
        },
        "warnings": warnings,
        "scalar_score_has_final_authority": False,
        "authority": {
            "automatic_merge": False,
            "automatic_publication": False,
            "automatic_scientific_promotion": False,
            "automatic_product_claim": False,
            "human_approval_required": True,
        },
    }


def render_markdown(report: Mapping[str, Any]) -> str:
    gates = _require_mapping(report, "gates")
    lines = [
        "# Ω-PRODUCTION-QUALITY-OBSERVATORY-T R0.1",
        "",
        f"**Decision:** `{report['decision']}`",
        "",
        "## Gates",
        "",
        "| Gate | Status |",
        "|---|---|",
    ]
    for name in ("volume", "integration", "wip", "external_science", "external_product"):
        gate = _require_mapping(gates, name)
        lines.append(f"| `{name}` | **{gate['status']}** |")

    lines.extend(
        [
            "",
            "## Warnings",
            "",
        ]
    )
    warnings = report.get("warnings", [])
    if warnings:
        lines.extend(f"- {warning}" for warning in warnings)
    else:
        lines.append("- None.")

    lines.extend(
        [
            "",
            "## OAK boundary",
            "",
            "A virtual plan is not execution. Synthetic execution is not external validation. "
            "A hash proves byte identity, not scientific truth. A scalar score has no final authority.",
            "",
        ]
    )
    return "\n".join(lines)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--snapshot", required=True)
    parser.add_argument("--policy", required=True)
    parser.add_argument("--output-json")
    parser.add_argument("--output-md")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    report = evaluate(load_json(args.snapshot), load_json(args.policy))
    rendered_json = json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True)
    print(rendered_json)

    if args.output_json:
        output_json = Path(args.output_json)
        output_json.parent.mkdir(parents=True, exist_ok=True)
        output_json.write_text(rendered_json + "\n", encoding="utf-8")
    if args.output_md:
        output_md = Path(args.output_md)
        output_md.parent.mkdir(parents=True, exist_ok=True)
        output_md.write_text(render_markdown(report), encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
