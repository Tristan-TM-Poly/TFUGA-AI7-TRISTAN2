from __future__ import annotations

from datetime import datetime, timezone
import json
from pathlib import Path

import pytest

from omega_company_outreach_t.foundation.canonical import CanonicalizationError, canonical_hash
from omega_company_outreach_t.foundation.contacts import RoleCategory
from omega_company_outreach_t.foundation.consent import ConsentBasis, ConsentScope
from omega_company_outreach_t.foundation.graph import (
    EdgeType,
    GraphEdge,
    GraphNode,
    Hyperedge,
    NodeType,
    RelationshipGraph,
    responsibility_hyperedge,
)
from omega_company_outreach_t.foundation.migration import MigrationIds
from omega_company_outreach_t.foundation.migration_runtime import (
    audit_migration_bundle,
    migrate_case_file,
)
from omega_company_outreach_t.foundation.opportunities import OpportunityType, StrategicSignals
from omega_company_outreach_t.foundation.organizations import OrganizationType
from omega_company_outreach_t.foundation.scenario_atlas import (
    AuthorityLevel,
    ExpectedDecision,
    RiskClass,
    ScenarioDimensions,
    audit_scenarios,
    decide,
    generate_scenarios,
    theoretical_cardinality,
)
from omega_company_outreach_t.foundation.scenario_runtime import (
    audit_atlas_directory,
    read_atlas,
    scenario_to_mapping,
    verify_determinism,
    write_atlas,
)
from omega_company_outreach_t.foundation.schemas import (
    audit_schema_catalog,
    schema_catalog,
    schema_definitions,
    write_schema_catalog,
)
from omega_company_outreach_t.foundation.contacts import ContactState, RoleCategory
from omega_company_outreach_t.foundation.consent import ConsentBasis, ConsentScope, ConsentState
from omega_company_outreach_t.foundation.identity import IdentityState
from omega_company_outreach_t.foundation.opportunities import CompanyUnit, OpportunityState, OpportunityType
from omega_company_outreach_t.foundation.organizations import OrganizationType, RelationshipState

NOW = datetime(2026, 8, 2, 20, 0, tzinfo=timezone.utc)
HASH_A = "sha256:" + "a" * 64
HASH_B = "sha256:" + "b" * 64


def test_relationship_graph_adds_nodes_edges_and_hyperedges():
    graph = RelationshipGraph()
    graph.add_node(GraphNode("tristan_research_foundry", NodeType.COMPANY, "Research Foundry"))
    graph.add_node(GraphNode("ORG-2026-0001", NodeType.ORGANIZATION, "University"))
    graph.add_node(GraphNode("OPP-2026-0001", NodeType.OPPORTUNITY, "Research pilot"))
    graph.add_edge(
        GraphEdge(
            edge_id="EDGE-0001",
            edge_type=EdgeType.TARGETS,
            source_id="OPP-2026-0001",
            target_id="ORG-2026-0001",
            confidence=0.9,
        )
    )
    graph.add_hyperedge(
        responsibility_hyperedge(
            hyperedge_id="HYPER-0001",
            opportunity_id="OPP-2026-0001",
            owner_company_id="tristan_research_foundry",
            contributor_company_ids=(),
        )
    )
    audit = graph.audit()
    assert audit.valid
    assert audit.node_count == 3
    assert audit.edge_count == 1
    assert audit.hyperedge_count == 1
    assert graph.shortest_path("OPP-2026-0001", "ORG-2026-0001") == (
        "OPP-2026-0001",
        "ORG-2026-0001",
    )


def test_graph_rejects_missing_edge_endpoints():
    graph = RelationshipGraph()
    graph.add_node(GraphNode("ORG-2026-0001", NodeType.ORGANIZATION, "Organization"))
    with pytest.raises(CanonicalizationError, match="endpoints"):
        graph.add_edge(
            GraphEdge(
                edge_id="EDGE-0001",
                edge_type=EdgeType.HAS_CONTACT,
                source_id="ORG-2026-0001",
                target_id="CNT-2026-0001",
            )
        )


def test_graph_detects_duplicate_semantic_edges():
    graph = RelationshipGraph()
    graph.add_node(GraphNode("ORG-2026-0001", NodeType.ORGANIZATION, "Organization"))
    graph.add_node(GraphNode("CNT-2026-0001", NodeType.CONTACT, "Contact"))
    graph.add_edge(
        GraphEdge("EDGE-0001", EdgeType.HAS_CONTACT, "ORG-2026-0001", "CNT-2026-0001")
    )
    graph.add_edge(
        GraphEdge("EDGE-0002", EdgeType.HAS_CONTACT, "ORG-2026-0001", "CNT-2026-0001")
    )
    assert not graph.audit().valid
    assert any("duplicate semantic edge" in error for error in graph.audit().errors)


def test_graph_subgraph_and_components_are_deterministic():
    graph = RelationshipGraph()
    for identifier, kind in (
        ("A", NodeType.COMPANY),
        ("B", NodeType.ORGANIZATION),
        ("C", NodeType.CONTACT),
        ("D", NodeType.ASSET),
    ):
        graph.add_node(GraphNode(identifier, kind, identifier))
    graph.add_edge(GraphEdge("E1", EdgeType.TARGETS, "A", "B"))
    graph.add_edge(GraphEdge("E2", EdgeType.HAS_CONTACT, "B", "C"))
    assert graph.connected_components() == (("D",), ("A", "B", "C"))
    subgraph = graph.subgraph(("A", "B", "C"))
    assert subgraph.audit().valid
    assert subgraph.shortest_path("A", "C") == ("A", "B", "C")


def test_hyperedge_requires_existing_participants():
    graph = RelationshipGraph()
    graph.add_node(GraphNode("A", NodeType.COMPANY, "A"))
    with pytest.raises(CanonicalizationError, match="missing nodes"):
        graph.add_hyperedge(
            Hyperedge(
                hyperedge_id="H1",
                relation="test",
                participant_ids=("A", "B"),
                roles={"A": "owner", "B": "target"},
                confidence=1.0,
            )
        )


def test_graph_json_output_has_stable_hash(tmp_path: Path):
    graph = RelationshipGraph()
    graph.add_node(GraphNode("A", NodeType.COMPANY, "A"))
    graph.add_node(GraphNode("B", NodeType.ORGANIZATION, "B"))
    graph.add_edge(GraphEdge("E1", EdgeType.TARGETS, "A", "B"))
    first = tmp_path / "first.json"
    second = tmp_path / "second.json"
    graph.write_json(first)
    graph.write_json(second)
    assert first.read_bytes() == second.read_bytes()
    payload = json.loads(first.read_text(encoding="utf-8"))
    assert payload["graph_hash"]


def _signals():
    return StrategicSignals(
        relevance=0.96,
        authority=0.78,
        problem_fit=0.90,
        asset_readiness=0.72,
        evidence=0.82,
        timing=0.88,
        reciprocity=0.86,
        expected_value=0.84,
        probability_response=0.62,
        probability_conversion=0.48,
        optionality=0.94,
        effort_cost=0.18,
        legal_risk=0.12,
        reputation_risk=0.10,
        privacy_risk=0.08,
        maintenance_cost=0.22,
        opportunity_cost=0.15,
    )


def _migration_ids():
    return MigrationIds(
        organization_id="ORG-2026-0001",
        contact_id="CNT-2026-0001",
        consent_id="CONSENT-2026-0001",
        opportunity_id="OPP-2026-0001",
        evidence_id="EVID-2026-0001",
        contact_evidence_id="EVID-2026-5001",
        event_ids=tuple(f"EVT-2026-000{index}" for index in range(1, 6)),
    )


def test_migrate_real_r02_case_to_canonical_bundle(tmp_path: Path):
    source = tmp_path / "source.json"
    source.write_text(
        json.dumps(
            {
                "case_id": "OUT-2026-0001",
                "company_unit": "tristan_parent_opco",
                "kind": "entrepreneurship",
                "target_organization": "Futurpreneur Canada",
                "recipient_hash": HASH_A,
                "subject": "Program guidance",
                "purpose": "Request non-binding program guidance.",
                "status": "sent",
                "sent_at": "2026-08-02",
                "provider_receipt_hash": HASH_B,
                "source_issue": 278,
                "follow_up_after": "2026-08-16",
                "legal_entity_claimed": False,
                "corporate_domain_verified": False,
            }
        ),
        encoding="utf-8",
    )
    destination = tmp_path / "migration.json"
    output = migrate_case_file(
        source,
        destination,
        ids=_migration_ids(),
        organization_type=OrganizationType.NONPROFIT,
        opportunity_type=OpportunityType.ENTREPRENEURSHIP_PROGRAM,
        role_category=RoleCategory.PROGRAM_MANAGER,
        consent_basis=ConsentBasis.EXISTING_NONBUSINESS_RELATIONSHIP,
        consent_scope=ConsentScope.PROGRAM_INFORMATION,
        strategic_signals=_signals(),
        proposed_asset_id="oakgate_company_validation",
        organization_domain="futurpreneur.ca",
    )
    assert destination.exists()
    assert audit_migration_bundle(output) == []
    assert output["organization"]["canonical_name"] == "Futurpreneur Canada"
    assert output["contact"]["private_email_ref"].startswith("vault://")
    assert output["opportunity"]["company_unit"] == "tristan_parent_opco"
    assert len(output["events"]) == 5
    assert output["migration_hash"].startswith("sha256:")


def test_migration_rejects_legacy_legal_entity_claim(tmp_path: Path):
    source = tmp_path / "source.json"
    source.write_text(
        json.dumps(
            {
                "case_id": "OUT-2026-0001",
                "company_unit": "tristan_parent_opco",
                "target_organization": "Example",
                "recipient_hash": HASH_A,
                "purpose": "Request guidance.",
                "sent_at": "2026-08-02",
                "provider_receipt_hash": HASH_B,
                "source_issue": 278,
                "legal_entity_claimed": True,
            }
        ),
        encoding="utf-8",
    )
    with pytest.raises(CanonicalizationError, match="manual migration"):
        migrate_case_file(
            source,
            tmp_path / "out.json",
            ids=_migration_ids(),
            organization_type=OrganizationType.NONPROFIT,
            opportunity_type=OpportunityType.ENTREPRENEURSHIP_PROGRAM,
            role_category=RoleCategory.PROGRAM_MANAGER,
            consent_basis=ConsentBasis.EXISTING_NONBUSINESS_RELATIONSHIP,
            consent_scope=ConsentScope.PROGRAM_INFORMATION,
            strategic_signals=_signals(),
            proposed_asset_id="asset",
        )


def test_schema_catalog_contains_versioned_foundation_objects(tmp_path: Path):
    definitions = schema_definitions()
    assert len(definitions) >= 12
    assert len({(item.name, item.version) for item in definitions}) == len(definitions)
    catalog = schema_catalog()
    assert catalog["schema_count"] == len(definitions)
    assert catalog["catalog_hash"].startswith("sha256:")
    generated = write_schema_catalog(tmp_path / "schemas")
    assert generated == catalog
    assert audit_schema_catalog(tmp_path / "schemas") == []


def test_schema_audit_detects_tampering(tmp_path: Path):
    directory = tmp_path / "schemas"
    write_schema_catalog(directory)
    target = next(directory.glob("*.schema.json"))
    payload = json.loads(target.read_text(encoding="utf-8"))
    payload["title"] = "Tampered"
    target.write_text(json.dumps(payload), encoding="utf-8")
    errors = audit_schema_catalog(directory)
    assert any("content mismatch" in error for error in errors)


def base_dimensions(**overrides):
    payload = {
        "company_unit": CompanyUnit.SOFTWARE,
        "organization_type": OrganizationType.SME,
        "opportunity_type": OpportunityType.SOFTWARE_PILOT,
        "identity_state": IdentityState.INTERNAL_ROLE,
        "organization_state": RelationshipState.QUALIFIED,
        "contact_state": ContactState.CONTACTABLE,
        "role_category": RoleCategory.ENGINEER,
        "consent_basis": ConsentBasis.LEGITIMATE_PROFESSIONAL_CONTEXT,
        "consent_scope": ConsentScope.SOFTWARE_PILOT,
        "consent_state": ConsentState.VALID,
        "opportunity_state": OpportunityState.QUALIFIED,
        "risk_class": RiskClass.LOW,
        "authority_level": AuthorityLevel.FOUNDER_APPROVAL,
        "evidence_band": 4,
        "strategic_score_band": 4,
    }
    payload.update(overrides)
    return ScenarioDimensions(**payload)


def test_scenario_decision_blocks_wrong_company():
    result = decide(base_dimensions(company_unit=CompanyUnit.RESEARCH))
    assert result.decision is ExpectedDecision.BLOCK
    assert result.expected_company is CompanyUnit.SOFTWARE


def test_scenario_decision_blocks_suppression():
    result = decide(base_dimensions(contact_state=ContactState.SUPPRESSED))
    assert result.decision is ExpectedDecision.BLOCK


def test_scenario_decision_requires_consent():
    result = decide(
        base_dimensions(consent_state=ConsentState.UNKNOWN, consent_basis=ConsentBasis.NONE)
    )
    assert result.decision is ExpectedDecision.REQUIRE_CONSENT


def test_scenario_decision_escalates_legal_risk():
    result = decide(
        base_dimensions(
            risk_class=RiskClass.LEGAL,
            authority_level=AuthorityLevel.FOUNDER_APPROVAL,
        )
    )
    assert result.decision is ExpectedDecision.REQUIRE_PROFESSIONAL_REVIEW


def test_scenario_decision_allows_only_preparation_for_internal_identity():
    result = decide(base_dimensions(identity_state=IdentityState.INTERNAL_ROLE))
    assert result.decision is ExpectedDecision.ALLOW_PREPARATION
    assert not result.requires_external_execution


def test_generated_scenarios_are_unique_and_cover_decisions():
    scenarios = tuple(generate_scenarios(count=2048, seed=42))
    assert len(scenarios) == 2048
    assert audit_scenarios(scenarios) == []
    assert len({scenario.scenario_hash for scenario in scenarios}) == 2048
    assert len({scenario.expectation.decision for scenario in scenarios}) == len(ExpectedDecision)


def test_scenario_mapping_supports_slots_dataclass():
    scenario = next(generate_scenarios(count=1, seed=1))
    payload = scenario_to_mapping(scenario)
    assert payload["scenario_id"] == scenario.scenario_id
    assert payload["scenario_hash"] == scenario.scenario_hash
    assert payload["dimensions"]["company_unit"] in {item.value for item in CompanyUnit}


def test_atlas_round_trip_and_manifest_audit(tmp_path: Path):
    directory = tmp_path / "atlas"
    manifest = write_atlas(directory, count=1024, seed=123, shard_size=128)
    assert manifest["scenario_count"] == 1024
    assert manifest["shard_count"] == 8
    scenarios = read_atlas(directory)
    assert len(scenarios) == 1024
    audit = audit_atlas_directory(directory)
    assert audit["valid"]
    assert audit["scenario_count"] == 1024


def test_atlas_detects_scenario_tampering(tmp_path: Path):
    directory = tmp_path / "atlas"
    write_atlas(directory, count=256, seed=123, shard_size=128)
    shard = directory / "scenarios-0000.jsonl"
    lines = shard.read_text(encoding="utf-8").splitlines()
    payload = json.loads(lines[0])
    payload["dimensions"]["evidence_band"] = 0
    lines[0] = json.dumps(payload)
    shard.write_text("\n".join(lines) + "\n", encoding="utf-8")
    with pytest.raises(CanonicalizationError, match="hash mismatch"):
        read_atlas(directory)


def test_atlas_is_deterministic():
    result = verify_determinism(count=1024, seed=20260802)
    assert result["deterministic"]
    assert result["first_hash"] == result["second_hash"]


def test_theoretical_cardinality_is_massive():
    assert theoretical_cardinality() > 100_000_000
