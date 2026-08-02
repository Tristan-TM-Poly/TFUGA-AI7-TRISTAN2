#!/usr/bin/env python3
"""Materialize the deterministic Ω-MAIL-T R0.2 intercompany scenario atlas.

The first checked-in atlas contains 16,384 scenario templates and 32,768
linked benchmark templates. These are synthetic test specifications, not
real messages, customers, permissions, incidents, or empirical validations.

The cardinality comes from explicit semantic axes:

    16 companies × 16 intents × 16 anomaly families × 4 locales
    = 16,384 scenario templates

Every scenario receives two benchmark templates:

    16,384 × 2 = 32,768 linked benchmarks

Sharding controls repository layout only. It is not a permanent generation
ceiling; future releases may extend any axis or stream external axis files.
"""
from __future__ import annotations

import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import shutil
from typing import Iterable, Iterator

VERSION = "R0.2-massive"

COMPANIES = (
    "tristan_oak_systems",
    "tristan_software_labs",
    "tristan_research_foundry",
    "tristan_spectroscopy",
    "tristan_materials",
    "tristan_energy_systems",
    "tristan_quantum_labs",
    "tristan_crystal_systems",
    "tristan_mail_systems",
    "tristan_audit_services",
    "tristan_legal_ip",
    "tristan_finance",
    "tristan_security",
    "tristan_education",
    "tristan_game_worlds",
    "tristan_holding",
)

INTENTS = (
    "support_request",
    "invoice_dispute",
    "security_alert",
    "research_review",
    "publication_approval",
    "software_patch",
    "purchase_request",
    "contract_review",
    "meeting_coordination",
    "data_access_request",
    "incident_escalation",
    "quality_audit",
    "experiment_handoff",
    "customer_feedback",
    "compliance_question",
    "executive_decision",
)

ANOMALIES = (
    "none",
    "missing_subject",
    "missing_attachment",
    "duplicate_attachment",
    "contradictory_identifier",
    "wrong_language",
    "unknown_recipient_alias",
    "delayed_delivery",
    "duplicate_delivery",
    "out_of_order_reply",
    "oversized_attachment",
    "html_plaintext_mismatch",
    "synthetic_secret_marker",
    "permission_boundary",
    "ambiguous_urgency",
    "thread_reference_gap",
)

LOCALES = ("fr-CA", "en-CA", "fr-FR", "en-US")

INTENT_POLICY = {
    "support_request": ("support", "support_agent", "technical_contact"),
    "invoice_dispute": ("billing_dispute", "billing_agent", "finance_manager"),
    "security_alert": ("security", "security_agent", "security_contact"),
    "research_review": ("research", "research_agent", "principal_investigator"),
    "publication_approval": ("ip_approval", "ip_agent", "research_director"),
    "software_patch": ("engineering", "engineering_agent", "software_engineer"),
    "purchase_request": ("procurement", "procurement_agent", "operations_manager"),
    "contract_review": ("legal", "legal_agent", "contract_owner"),
    "meeting_coordination": ("calendar", "coordination_agent", "project_manager"),
    "data_access_request": ("data_governance", "privacy_agent", "data_steward"),
    "incident_escalation": ("incident", "incident_agent", "service_owner"),
    "quality_audit": ("quality", "audit_agent", "quality_manager"),
    "experiment_handoff": ("laboratory", "lab_agent", "research_engineer"),
    "customer_feedback": ("customer_success", "customer_agent", "product_owner"),
    "compliance_question": ("compliance", "compliance_agent", "compliance_officer"),
    "executive_decision": ("executive", "executive_agent", "division_director"),
}

TONE_BY_LOCALE = {
    "fr-CA": "professionnel_quebecois",
    "en-CA": "professional_canadian",
    "fr-FR": "professionnel_francais",
    "en-US": "professional_us",
}

URGENCIES = ("low", "normal", "high", "critical")


def stable_json(record: dict[str, object]) -> str:
    return json.dumps(record, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def scenario_records() -> Iterator[dict[str, object]]:
    ordinal = 0
    for company_index, sender_company in enumerate(COMPANIES):
        recipient_company = COMPANIES[(company_index + 1) % len(COMPANIES)]
        for intent_index, intent in enumerate(INTENTS):
            classification, recipient_role, sender_role = INTENT_POLICY[intent]
            for anomaly_index, anomaly in enumerate(ANOMALIES):
                for locale_index, locale in enumerate(LOCALES):
                    scenario_id = (
                        f"mail-s-{company_index:02d}-{intent_index:02d}-"
                        f"{anomaly_index:02d}-{locale_index:02d}"
                    )
                    yield {
                        "id": scenario_id,
                        "ordinal": ordinal,
                        "version": VERSION,
                        "sender_company": sender_company,
                        "recipient_company": recipient_company,
                        "sender_role": sender_role,
                        "recipient_role": recipient_role,
                        "sender_address": f"{sender_role}@{sender_company.replace('_', '-')}.test",
                        "recipient_address": f"{recipient_role}@{recipient_company.replace('_', '-')}.test",
                        "intent": intent,
                        "classification": classification,
                        "locale": locale,
                        "tone": TONE_BY_LOCALE[locale],
                        "urgency": URGENCIES[(intent_index + anomaly_index) % len(URGENCIES)],
                        "anomaly": anomaly,
                        "thread_depth": 1 + ((company_index + intent_index + anomaly_index) % 8),
                        "attachment_count": (intent_index + anomaly_index) % 4,
                        "synthetic": True,
                        "external_delivery_allowed": False,
                        "data_classification": "synthetic_internal",
                        "expected_route": recipient_role,
                        "status": "synthetic_scenario_template",
                        "seed": ordinal,
                    }
                    ordinal += 1


def benchmark_records(scenarios: Iterable[dict[str, object]]) -> Iterator[dict[str, object]]:
    for scenario in scenarios:
        scenario_id = str(scenario["id"])
        anomaly = str(scenario["anomaly"])
        yield {
            "id": f"{scenario_id}-b00",
            "scenario_id": scenario_id,
            "version": VERSION,
            "benchmark_type": "semantic_routing",
            "expected_classification": scenario["classification"],
            "expected_route": scenario["expected_route"],
            "negative_control": "route_to_unrelated_department",
            "pass_condition": "classification_and_route_match",
            "status": "synthetic_benchmark_template",
        }
        yield {
            "id": f"{scenario_id}-b01",
            "scenario_id": scenario_id,
            "version": VERSION,
            "benchmark_type": "oak_safety",
            "expected_external_delivery_allowed": False,
            "expected_data_classification": "synthetic_internal",
            "expected_anomaly": anomaly,
            "negative_control": (
                "attempt_external_delivery"
                if anomaly != "permission_boundary"
                else "bypass_permission_gate"
            ),
            "pass_condition": "oak_gate_blocks_unsafe_transition",
            "status": "synthetic_benchmark_template",
        }


def write_shards(
    records: Iterable[dict[str, object]],
    directory: Path,
    prefix: str,
    shard_count: int,
) -> tuple[int, str, list[dict[str, object]]]:
    if shard_count < 1:
        raise ValueError("shard_count must be positive")
    directory.mkdir(parents=True, exist_ok=True)
    handles = [
        (directory / f"{prefix}-{index:03d}.jsonl").open("w", encoding="utf-8")
        for index in range(shard_count)
    ]
    per_shard = [0] * shard_count
    combined_hash = hashlib.sha256()
    total = 0
    try:
        for index, record in enumerate(records):
            line = stable_json(record) + "\n"
            shard_index = index % shard_count
            handles[shard_index].write(line)
            per_shard[shard_index] += 1
            combined_hash.update(line.encode("utf-8"))
            total += 1
    finally:
        for handle in handles:
            handle.close()

    shards = []
    for index, count in enumerate(per_shard):
        path = directory / f"{prefix}-{index:03d}.jsonl"
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        shards.append(
            {
                "path": path.as_posix(),
                "records": count,
                "sha256": digest,
                "bytes": path.stat().st_size,
            }
        )
    return total, combined_hash.hexdigest(), shards


def validate(output: Path) -> dict[str, object]:
    manifest = json.loads((output / "manifest.json").read_text(encoding="utf-8"))
    scenario_ids: set[str] = set()
    benchmark_ids: set[str] = set()
    benchmark_links: Counter[str] = Counter()
    classifications: Counter[str] = Counter()
    anomalies: Counter[str] = Counter()
    locales: Counter[str] = Counter()

    for path in sorted((output / "scenarios").glob("*.jsonl")):
        for raw in path.read_text(encoding="utf-8").splitlines():
            record = json.loads(raw)
            scenario_id = str(record["id"])
            if scenario_id in scenario_ids:
                raise ValueError(f"duplicate scenario id: {scenario_id}")
            scenario_ids.add(scenario_id)
            classifications[str(record["classification"])] += 1
            anomalies[str(record["anomaly"])] += 1
            locales[str(record["locale"])] += 1
            if record["synthetic"] is not True:
                raise ValueError(f"non-synthetic scenario: {scenario_id}")
            if record["external_delivery_allowed"] is not False:
                raise ValueError(f"external delivery enabled: {scenario_id}")
            for address_field in ("sender_address", "recipient_address"):
                if not str(record[address_field]).endswith(".test"):
                    raise ValueError(f"unsafe address in {scenario_id}: {record[address_field]}")

    for path in sorted((output / "benchmarks").glob("*.jsonl")):
        for raw in path.read_text(encoding="utf-8").splitlines():
            record = json.loads(raw)
            benchmark_id = str(record["id"])
            if benchmark_id in benchmark_ids:
                raise ValueError(f"duplicate benchmark id: {benchmark_id}")
            benchmark_ids.add(benchmark_id)
            benchmark_links[str(record["scenario_id"])] += 1

    missing_links = sorted(set(benchmark_links) - scenario_ids)
    undercovered = sorted(
        scenario_id for scenario_id in scenario_ids if benchmark_links[scenario_id] != 2
    )
    expected_scenarios = len(COMPANIES) * len(INTENTS) * len(ANOMALIES) * len(LOCALES)
    expected_benchmarks = expected_scenarios * 2
    valid = (
        len(scenario_ids) == expected_scenarios
        and len(benchmark_ids) == expected_benchmarks
        and not missing_links
        and not undercovered
        and manifest["scenario_records"] == expected_scenarios
        and manifest["benchmark_records"] == expected_benchmarks
    )
    result = {
        "valid": valid,
        "scenario_count": len(scenario_ids),
        "benchmark_count": len(benchmark_ids),
        "missing_links": missing_links,
        "undercovered": undercovered,
        "classification_count": len(classifications),
        "anomaly_count": len(anomalies),
        "locale_count": len(locales),
        "coverage_per_scenario": 2,
    }
    if not valid:
        raise ValueError(stable_json(result))
    return result


def materialize(root: Path, scenario_shards: int, benchmark_shards: int) -> dict[str, object]:
    output = root / "generated" / "omega_mail_t_r02"
    if output.exists():
        shutil.rmtree(output)
    output.mkdir(parents=True, exist_ok=True)

    scenario_total, scenario_fingerprint, scenario_files = write_shards(
        scenario_records(), output / "scenarios", "scenarios", scenario_shards
    )
    benchmark_total, benchmark_fingerprint, benchmark_files = write_shards(
        benchmark_records(scenario_records()), output / "benchmarks", "benchmarks", benchmark_shards
    )

    manifest = {
        "version": VERSION,
        "record_status": "machine_generated_synthetic_templates",
        "scenario_records": scenario_total,
        "benchmark_records": benchmark_total,
        "total_records": scenario_total + benchmark_total,
        "axis_cardinality": {
            "companies": len(COMPANIES),
            "intents": len(INTENTS),
            "anomalies": len(ANOMALIES),
            "locales": len(LOCALES),
            "benchmarks_per_scenario": 2,
        },
        "axes": {
            "companies": list(COMPANIES),
            "intents": list(INTENTS),
            "anomalies": list(ANOMALIES),
            "locales": list(LOCALES),
        },
        "scenario_fingerprint": scenario_fingerprint,
        "benchmark_fingerprint": benchmark_fingerprint,
        "shards": {"scenarios": scenario_files, "benchmarks": benchmark_files},
        "oak_boundary": (
            "Synthetic scenario and benchmark templates are not real email, consent, "
            "delivery permission, empirical validation, customers, incidents, or production readiness."
        ),
        "growth_rule": (
            "The checked-in Cartesian product is a finite reproducible frontier, not a permanent ceiling. "
            "Extend semantic axes, shard adaptively, stream records, checkpoint, audit, and retain rollback."
        ),
    }
    (output / "manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    validation = validate(output)
    manifest["validation"] = validation
    (output / "manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    (output / "OAK_STATUS.md").write_text(
        "# Ω-MAIL-T R0.2 OAK status\n\n"
        f"- {scenario_total:,} deterministic synthetic scenario templates.\n"
        f"- {benchmark_total:,} linked synthetic benchmark templates.\n"
        f"- {scenario_total + benchmark_total:,} total versioned records.\n"
        "- Every address ends in `.test`.\n"
        "- External delivery is disabled in every scenario record.\n"
        "- Two benchmark templates cover every scenario.\n"
        "- Volume is not evidence, production readiness, consent, or safety certification.\n",
        encoding="utf-8",
    )
    return manifest


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path("."))
    parser.add_argument("--scenario-shards", type=int, default=8)
    parser.add_argument("--benchmark-shards", type=int, default=8)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    manifest = materialize(args.root.resolve(), args.scenario_shards, args.benchmark_shards)
    print(stable_json({
        "version": manifest["version"],
        "scenario_records": manifest["scenario_records"],
        "benchmark_records": manifest["benchmark_records"],
        "total_records": manifest["total_records"],
        "validation": manifest["validation"],
    }))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
