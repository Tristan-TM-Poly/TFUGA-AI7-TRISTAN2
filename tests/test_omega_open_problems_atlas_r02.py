from __future__ import annotations

import json
from pathlib import Path

import jsonschema
import pytest

from omega_open_problems_atlas.r02.benchmark import (
    logical_frontier_count,
    method_bank,
    run_benchmark,
    synthetic_leads,
)
from omega_open_problems_atlas.r02.campaign import allocate_campaign, campaign_manifest
from omega_open_problems_atlas.r02.competition import (
    competition_count,
    evaluate_policy,
    research_open_count,
)
from omega_open_problems_atlas.r02.dedupe import (
    exact_duplicate_groups,
    near_duplicate_findings,
)
from omega_open_problems_atlas.r02.formal import audit_text, promotion_allowed
from omega_open_problems_atlas.r02.intake import (
    IntakePolicy,
    audit_sensitive_fields,
    ingest_records,
    snapshot_file,
)
from omega_open_problems_atlas.r02.merkle import (
    digest_text,
    inclusion_proof,
    merkle_root,
    verify_inclusion,
)
from omega_open_problems_atlas.r02.models import (
    CompetitionPolicy,
    EvidenceClass,
    EvidenceReceipt,
    FormalStatus,
    LeadStatus,
    ProblemLead,
)
from omega_open_problems_atlas.r02.obligations import (
    OBLIGATION_OPERATORS,
    compile_obligations,
    stream_obligations,
)
from omega_open_problems_atlas.r02.store import AtlasStore
from omega_open_problems_atlas.r02.transfer import (
    candidate_transfers,
    compile_transfer_edges,
    transfer_summary,
)


def _lead(identifier: str = "P1", statement: str = "Determine whether a finite fixture exists") -> ProblemLead:
    return ProblemLead(
        lead_id=identifier,
        source_id="TEST",
        source_locator=f"fixture://{identifier}",
        title=f"Test problem {identifier}",
        statement_summary=statement,
        domains=("number_theory", "combinatorics"),
        kind="RESEARCH_PROBLEM",
        lead_status=LeadStatus.SOURCE_REPORTED,
        methods=("OPA-METHOD-0000",),
        independently_checked_open=False,
        solution_claimed=False,
    )


def test_problem_lead_hashes_are_deterministic_and_safe() -> None:
    left = _lead()
    right = _lead()
    assert left.statement_hash() == right.statement_hash()
    assert left.canonical_hash() == right.canonical_hash()
    assert len(left.canonical_hash()) == 64
    assert left.independently_checked_open is False
    assert left.solution_claimed is False


def test_merkle_proof_detects_tampering() -> None:
    leaves = [digest_text(f"leaf-{index}") for index in range(11)]
    root = merkle_root(leaves)
    proof = inclusion_proof(leaves, 6)
    assert verify_inclusion(leaves[6], proof, root)
    assert not verify_inclusion(digest_text("tampered"), proof, root)


def test_exact_and_near_duplicate_detection() -> None:
    leads = (
        _lead("A", "Is there a graph with property alpha?"),
        _lead("B", "Is there a graph with property alpha?"),
        _lead("C", "Is there a graph having property alpha and beta?"),
    )
    assert exact_duplicate_groups(leads) == (("A", "B"),)
    findings = near_duplicate_findings(leads, threshold=0.55)
    assert any(item.left_id == "A" and item.right_id == "C" for item in findings)
    assert all(0.0 <= item.similarity <= 1.0 for item in findings)


def test_sensitive_intake_fields_fail_closed(tmp_path: Path) -> None:
    path = tmp_path / "snapshot.json"
    path.write_text(
        json.dumps(
            [
                {
                    "source_locator": "x/1",
                    "title": "A lead",
                    "statement_summary": "A source-reported question",
                    "domains": ["algebra"],
                    "bank_account": "must-never-enter-atlas",
                }
            ]
        ),
        encoding="utf-8",
    )
    policy = IntakePolicy(
        source_id="TEST",
        authority_class="FIXTURE",
        license_class="FIXTURE",
        allow_statement_summary=True,
        allow_full_statement=False,
        require_status_recheck=True,
        require_literature_check=True,
    )
    snapshot = snapshot_file(path, policy, "2026-08-03T00:00:00Z")
    records = json.loads(path.read_text(encoding="utf-8"))
    leads, report = ingest_records(records, policy, snapshot)
    assert leads == ()
    assert report.accepted_count == 0
    assert report.rejected_count == 1
    assert any("forbidden sensitive field" in item for item in report.findings)
    assert audit_sensitive_fields(tuple(records))


def test_intake_tracks_duplicate_locators_and_status(tmp_path: Path) -> None:
    path = tmp_path / "snapshot.json"
    records = [
        {
            "lead_id": "L1",
            "source_locator": "item/1",
            "title": "Lead one",
            "statement_summary": "Investigate a source-reported relation",
            "domains": ["topology"],
        },
        {
            "lead_id": "L2",
            "source_locator": "item/1",
            "title": "Lead duplicate",
            "statement_summary": "A duplicate source locator",
            "domains": ["topology"],
        },
    ]
    path.write_text(json.dumps(records), encoding="utf-8")
    policy = IntakePolicy(
        source_id="SOURCE",
        authority_class="CURATED",
        license_class="METADATA_ONLY",
        allow_statement_summary=True,
        allow_full_statement=False,
        require_status_recheck=True,
        require_literature_check=True,
    )
    snapshot = snapshot_file(path, policy, "2026-08-03T00:00:00Z")
    leads, report = ingest_records(records, policy, snapshot)
    assert len(leads) == 1
    assert leads[0].lead_status is LeadStatus.STATUS_RECHECK_REQUIRED
    assert leads[0].independently_checked_open is False
    assert report.duplicate_locator_count == 1


def test_compile_obligations_covers_64_operators() -> None:
    obligations = compile_obligations(_lead())
    assert len(OBLIGATION_OPERATORS) == 64
    assert len(obligations) == 64
    assert len({item.obligation_id for item in obligations}) == 64
    assert all(not item.universal_claim for item in obligations)
    assert any(EvidenceClass.FORMAL_CHECK in item.expected_evidence for item in obligations)


def test_stream_obligations_allocates_exact_finite_budget() -> None:
    obligations = tuple(stream_obligations((_lead("A"), _lead("B")), 10_001))
    assert len(obligations) == 10_001
    assert sum(item.finite_budget_units for item in obligations) == 10_001
    assert len({item.obligation_id for item in obligations}) == 10_001


def test_campaign_allocates_exact_budget_without_truth_probability() -> None:
    leads = (_lead("A"), _lead("B"))
    obligations = tuple(stream_obligations(leads, 32))
    allocations = allocate_campaign(leads, obligations, 127)
    manifest = campaign_manifest(allocations)
    assert manifest["allocated_units"] == 127
    assert manifest["permanent_total_cap"] is None
    assert manifest["priority_score_is_not_truth_probability"] is True
    assert manifest["solution_claimed"] is False


def test_formal_audit_blocks_placeholders() -> None:
    incomplete = audit_text("candidate.lean", "theorem t : True := by\n  sorry\n")
    assert incomplete.status is FormalStatus.PLACEHOLDERS_PRESENT
    assert incomplete.placeholder_lines == (2,)
    assert not promotion_allowed(incomplete)
    checked = audit_text(
        "candidate.lean",
        "theorem t : True := by\n  trivial\n",
        kernel_check_claimed=True,
    )
    assert checked.status is FormalStatus.KERNEL_CHECKED_LOCAL
    assert promotion_allowed(checked)


def test_competitions_are_not_counted_as_open_research() -> None:
    research = _lead("R")
    checked = ProblemLead(
        **{
            **research.__dict__,
            "lead_id": "OPEN",
            "source_locator": "fixture://OPEN",
            "lead_status": LeadStatus.INDEPENDENTLY_CHECKED_OPEN,
            "independently_checked_open": True,
        }
    )
    competition = ProblemLead(
        **{
            **research.__dict__,
            "lead_id": "COMP",
            "source_locator": "fixture://COMP",
            "kind": "COMPETITION_PROBLEM",
            "lead_status": LeadStatus.INDEPENDENTLY_CHECKED_OPEN,
            "independently_checked_open": True,
        }
    )
    assert research_open_count((research, checked, competition)) == 1
    assert competition_count((research, checked, competition)) == 1


def test_competition_policy_blocks_automatic_submission() -> None:
    decision = evaluate_policy(
        CompetitionPolicy(
            competition_id="C",
            organizer="Organizer",
            canonical_url="https://example.invalid/competition",
            problem_class="FIXTURE",
            automated_submission_allowed=False,
            redistribution_allowed=False,
        )
    )
    assert "automated_submission" in decision.blocked_actions
    assert "automated_identity_bound_submission" in decision.blocked_actions
    assert decision.human_review_required


def test_sqlite_store_checkpoint_and_merkle(tmp_path: Path) -> None:
    leads = synthetic_leads(32)
    methods = method_bank(8)
    obligations = tuple(stream_obligations(leads, 257))
    path = tmp_path / "atlas.sqlite3"
    with AtlasStore(path) as store:
        store.insert_leads(leads)
        with store.transaction():
            for method in methods:
                store.upsert_method(method)
        store.insert_obligations(obligations)
        receipt = EvidenceReceipt(
            receipt_id="REC-1",
            subject_id="OPA-SYN-00000000",
            evidence_class=EvidenceClass.COMPUTATION,
            artifact_sha256="0" * 64,
            command="pytest fixture",
            environment="python-test",
            observed_at="2026-08-03T00:00:00Z",
            result="PASS_FINITE_FIXTURE",
        )
        with store.transaction():
            store.append_receipt(receipt)
        checkpoint = store.checkpoint("CP-1", "2026-08-03T00:00:00Z")
        assert checkpoint["lead_count"] == 32
        assert checkpoint["method_count"] == 8
        assert checkpoint["obligation_count"] == 257
        assert checkpoint["receipt_count"] == 1
        assert len(checkpoint["merkle_root"]) == 64
        assert store.independently_checked_open_count() == 0
        assert store.solution_claim_count() == 0


def test_transfer_edges_require_round_trip_and_start_unvalidated() -> None:
    leads = synthetic_leads(64)
    methods = method_bank(8)
    candidates = candidate_transfers(leads, methods, threshold=0.1, max_pairs_per_method=5)
    edges = compile_transfer_edges(candidates)
    summary = transfer_summary(edges)
    assert edges
    assert summary["edge_count"] == len(edges)
    assert summary["validated_count"] == 0
    assert summary["round_trip_required_count"] == len(edges)
    assert all(edge.round_trip_required and not edge.transfer_validated for edge in edges)


def test_logical_frontier_is_large_but_not_materialized() -> None:
    assert logical_frontier_count() == 268_435_456


def test_small_benchmark_is_deterministic_and_separated(tmp_path: Path) -> None:
    first = run_benchmark(
        lead_count=128,
        obligation_budget=4096,
        transfer_lead_sample=64,
        sqlite_path=tmp_path / "first.sqlite3",
    )
    second = run_benchmark(
        lead_count=128,
        obligation_budget=4096,
        transfer_lead_sample=64,
        sqlite_path=tmp_path / "second.sqlite3",
    )
    assert first == second
    assert first["status"] == "CERTIFIED_SOFTWARE_RESEARCH_FIXTURES_R0_2"
    assert first["counts"]["leads"] == 128
    assert first["counts"]["methods"] == 128
    assert first["counts"]["obligations"] == 4096
    assert first["counts"]["independently_checked_open"] == 0
    assert first["counts"]["solution_claims"] == 0
    assert first["separation"]["research_open_count"] == 0
    assert first["merkle"]["sample_proof_valid"] is True
    assert first["permanent_total_cap"] is None
    assert first["generated_fixture_is_not_open_problem"] is True
    assert first["finite_computation_is_not_proof"] is True
    assert first["solution_claimed"] is False


def test_r02_schemas_and_data_catalogs() -> None:
    for path in sorted(Path("schemas").glob("open_problems_*_r02.schema.json")):
        schema = json.loads(path.read_text(encoding="utf-8"))
        jsonschema.Draft202012Validator.check_schema(schema)
    connectors = json.loads(
        Path("data/open_problems_atlas/r02/source_connectors.json").read_text(encoding="utf-8")
    )
    methods = json.loads(
        Path("data/open_problems_atlas/r02/method_families.json").read_text(encoding="utf-8")
    )
    competitions = json.loads(
        Path("data/open_problems_atlas/r02/competition_policy_seed.json").read_text(encoding="utf-8")
    )
    assert len(connectors["connectors"]) >= 20
    assert len(methods["families"]) == 16
    assert len(competitions["policies"]) >= 7
    assert connectors["global_boundaries"]["automatic_open_status_promotion"] is False
    assert competitions["global_boundaries"]["external_submission_performed"] is False


def test_benchmark_validates_against_schema(tmp_path: Path) -> None:
    report = run_benchmark(
        lead_count=64,
        obligation_budget=1024,
        transfer_lead_sample=32,
        sqlite_path=tmp_path / "schema.sqlite3",
    )
    schema = json.loads(
        Path("schemas/open_problems_benchmark_r02.schema.json").read_text(encoding="utf-8")
    )
    jsonschema.validate(report, schema)


def test_invalid_budgets_fail_closed() -> None:
    with pytest.raises(ValueError):
        tuple(stream_obligations((_lead(),), -1))
    with pytest.raises(ValueError):
        run_benchmark(lead_count=0, obligation_budget=1)
    with pytest.raises(ValueError):
        run_benchmark(lead_count=1, obligation_budget=-1)
