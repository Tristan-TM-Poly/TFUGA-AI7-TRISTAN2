from __future__ import annotations

from dataclasses import asdict
from enum import Enum
import json
from pathlib import Path
from typing import Any, Iterable

from .canonical import CanonicalizationError, canonical_hash, canonical_mapping
from .scenario_atlas import (
    AuthorityLevel,
    ExpectedDecision,
    OakScenario,
    RiskClass,
    ScenarioDimensions,
    ScenarioExpectation,
    audit_scenarios,
    decide,
    generate_scenarios,
    scenario_manifest,
    theoretical_cardinality,
)
from .consent import ConsentBasis, ConsentScope, ConsentState
from .contacts import ContactState, RoleCategory
from .identity import IdentityState
from .opportunities import CompanyUnit, OpportunityState, OpportunityType
from .organizations import OrganizationType, RelationshipState


def scenario_to_mapping(scenario: OakScenario) -> dict[str, Any]:
    dimensions = {
        key: value.value if isinstance(value, Enum) else value
        for key, value in asdict(scenario.dimensions).items()
    }
    expectation = {
        "decision": scenario.expectation.decision.value,
        "reasons": list(scenario.expectation.reasons),
        "requires_event": scenario.expectation.requires_event,
        "requires_external_execution": scenario.expectation.requires_external_execution,
        "expected_company": scenario.expectation.expected_company.value,
    }
    return {
        "scenario_id": scenario.scenario_id,
        "dimensions": dimensions,
        "expectation": expectation,
        "generator_version": scenario.generator_version,
        "scenario_hash": scenario.scenario_hash,
    }


def write_atlas(
    directory: Path,
    *,
    count: int = 8192,
    seed: int = 20260802,
    shard_size: int = 512,
) -> dict[str, Any]:
    if count < 1 or shard_size < 1:
        raise CanonicalizationError("count and shard_size must be positive")
    scenarios = tuple(generate_scenarios(count=count, seed=seed))
    errors = audit_scenarios(scenarios)
    if errors:
        raise CanonicalizationError("scenario audit failed: " + "; ".join(errors))
    directory.mkdir(parents=True, exist_ok=True)
    expected_names: set[str] = set()
    for index in range(0, len(scenarios), shard_size):
        name = f"scenarios-{index // shard_size:04d}.jsonl"
        expected_names.add(name)
        shard_path = directory / name
        shard = scenarios[index : index + shard_size]
        shard_path.write_text(
            "\n".join(
                json.dumps(
                    canonical_mapping(scenario_to_mapping(item)),
                    ensure_ascii=False,
                    sort_keys=True,
                    separators=(",", ":"),
                )
                for item in shard
            )
            + "\n",
            encoding="utf-8",
        )
    for stale in directory.glob("scenarios-*.jsonl"):
        if stale.name not in expected_names:
            stale.unlink()
    manifest = scenario_manifest(scenarios, seed=seed)
    manifest.update(
        {
            "shard_size": shard_size,
            "shard_count": (len(scenarios) + shard_size - 1) // shard_size,
            "runtime": "canonical-v2",
        }
    )
    (directory / "manifest.json").write_text(
        json.dumps(canonical_mapping(manifest), ensure_ascii=False, sort_keys=True, indent=2),
        encoding="utf-8",
    )
    return manifest


def scenario_from_mapping(payload: dict[str, Any]) -> OakScenario:
    dimensions_payload = payload["dimensions"]
    expectation_payload = payload["expectation"]
    dimensions = ScenarioDimensions(
        company_unit=CompanyUnit(dimensions_payload["company_unit"]),
        organization_type=OrganizationType(dimensions_payload["organization_type"]),
        opportunity_type=OpportunityType(dimensions_payload["opportunity_type"]),
        identity_state=IdentityState(dimensions_payload["identity_state"]),
        organization_state=RelationshipState(dimensions_payload["organization_state"]),
        contact_state=ContactState(dimensions_payload["contact_state"]),
        role_category=RoleCategory(dimensions_payload["role_category"]),
        consent_basis=ConsentBasis(dimensions_payload["consent_basis"]),
        consent_scope=ConsentScope(dimensions_payload["consent_scope"]),
        consent_state=ConsentState(dimensions_payload["consent_state"]),
        opportunity_state=OpportunityState(dimensions_payload["opportunity_state"]),
        risk_class=RiskClass(dimensions_payload["risk_class"]),
        authority_level=AuthorityLevel(dimensions_payload["authority_level"]),
        evidence_band=int(dimensions_payload["evidence_band"]),
        strategic_score_band=int(dimensions_payload["strategic_score_band"]),
    )
    expectation = ScenarioExpectation(
        decision=ExpectedDecision(expectation_payload["decision"]),
        reasons=tuple(str(item) for item in expectation_payload["reasons"]),
        requires_event=bool(expectation_payload["requires_event"]),
        requires_external_execution=bool(expectation_payload["requires_external_execution"]),
        expected_company=CompanyUnit(expectation_payload["expected_company"]),
    )
    scenario = OakScenario(
        scenario_id=str(payload["scenario_id"]),
        dimensions=dimensions,
        expectation=expectation,
        generator_version=str(payload.get("generator_version", "1.0")),
    )
    if payload.get("scenario_hash") != scenario.scenario_hash:
        raise CanonicalizationError(f"scenario hash mismatch: {scenario.scenario_id}")
    return scenario


def read_atlas(directory: Path) -> tuple[OakScenario, ...]:
    scenarios: list[OakScenario] = []
    for path in sorted(directory.glob("scenarios-*.jsonl")):
        for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
            if not line.strip():
                continue
            try:
                payload = json.loads(line)
            except json.JSONDecodeError as exc:
                raise CanonicalizationError(
                    f"{path.name}:{line_number} contains invalid JSON: {exc}"
                ) from exc
            if not isinstance(payload, dict):
                raise CanonicalizationError(f"{path.name}:{line_number} must contain an object")
            scenarios.append(scenario_from_mapping(payload))
    return tuple(scenarios)


def audit_atlas_directory(directory: Path) -> dict[str, Any]:
    scenarios = read_atlas(directory)
    errors = audit_scenarios(scenarios)
    manifest_path = directory / "manifest.json"
    if not manifest_path.exists():
        errors.append("manifest.json is missing")
        manifest: dict[str, Any] = {}
    else:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    seed = int(manifest.get("seed", 20260802))
    regenerated = scenario_manifest(scenarios, seed=seed)
    for key in (
        "scenario_count",
        "theoretical_cardinality",
        "decision_counts",
        "first_hash",
        "last_hash",
        "ordered_scenario_hash",
    ):
        if manifest.get(key) != regenerated.get(key):
            errors.append(f"manifest mismatch for {key}")
    shard_files = sorted(directory.glob("scenarios-*.jsonl"))
    if manifest.get("shard_count") != len(shard_files):
        errors.append("manifest shard_count mismatch")
    return {
        "valid": not errors,
        "errors": errors,
        "scenario_count": len(scenarios),
        "shard_count": len(shard_files),
        "theoretical_cardinality": theoretical_cardinality(),
        "manifest_hash": canonical_hash(manifest),
    }


def verify_determinism(
    *, count: int = 8192, seed: int = 20260802
) -> dict[str, Any]:
    first = tuple(generate_scenarios(count=count, seed=seed))
    second = tuple(generate_scenarios(count=count, seed=seed))
    first_hash = canonical_hash([scenario.scenario_hash for scenario in first])
    second_hash = canonical_hash([scenario.scenario_hash for scenario in second])
    return {
        "deterministic": first_hash == second_hash,
        "first_hash": first_hash,
        "second_hash": second_hash,
        "scenario_count": count,
    }
