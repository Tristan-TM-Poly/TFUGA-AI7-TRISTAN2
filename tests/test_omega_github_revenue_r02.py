from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

from omega_github_revenue_t.atlas import (
    AtlasEdge,
    AtlasNode,
    build_revenue_atlas,
    default_system_atlas,
)
from omega_github_revenue_t.authorization import (
    AuditAuthorization,
    AuthorizationError,
    Operation,
)
from omega_github_revenue_t.campaign import (
    CampaignConfig,
    run_campaign,
    stable_shard,
    synthetic_artifacts,
)
from omega_github_revenue_t.conversion import (
    FunnelSnapshot,
    analyze_funnel,
    posterior,
    recommend_funnel_action,
)
from omega_github_revenue_t.ledger import SensitiveDataError
from omega_github_revenue_t.models import SponsorTier
from omega_github_revenue_t.oakgate import run_oakgate
from omega_github_revenue_t.portfolio import (
    PortfolioCandidate,
    allocate_portfolio,
    dependency_order,
    pareto_front,
)
from omega_github_revenue_t.pricing import (
    DeliveryEstimate,
    delivery_economics,
    price_envelope,
)
from omega_github_revenue_t.privacy import (
    redact_text,
    reject_secret_values,
    scan_payload,
    scan_text,
)
from omega_github_revenue_t.profile import (
    ProjectCard,
    SponsorProfile,
    validate_profile,
    write_profile_bundle,
)
from omega_github_revenue_t.reconciliation import ProviderEvent, reconcile_events
from omega_github_revenue_t.repository_audit import (
    AuditPolicy,
    audit_repository,
    render_markdown,
)
from omega_github_revenue_t.store import CampaignStore
from omega_github_revenue_t.transparency import (
    build_manifest,
    digest_payload,
    merkle_proof,
    merkle_root,
    verify_merkle_proof,
)


def authorization(root: Path, **overrides) -> AuditAuthorization:
    now = datetime.now(timezone.utc)
    data = {
        "authorization_id": "AUTH-1",
        "repository_id": str(root.resolve()),
        "granted_by": "owner",
        "granted_at": (now - timedelta(minutes=1)).isoformat(),
        "expires_at": (now + timedelta(hours=1)).isoformat(),
        "operations": tuple(Operation),
        "explicitly_authorized": True,
    }
    data.update(overrides)
    return AuditAuthorization(**data)


def make_repository(tmp_path: Path) -> Path:
    root = tmp_path / "repo"
    root.mkdir()
    (root / "README.md").write_text("# Demo\n", encoding="utf-8")
    (root / "LICENSE").write_text("MIT placeholder\n", encoding="utf-8")
    (root / "SECURITY.md").write_text("Report privately\n", encoding="utf-8")
    (root / "src").mkdir()
    (root / "src" / "app.py").write_text("print('ok')\n", encoding="utf-8")
    (root / "tests").mkdir()
    (root / "tests" / "test_app.py").write_text(
        "def test_ok(): assert True\n",
        encoding="utf-8",
    )
    (root / ".github").mkdir()
    (root / ".github" / "workflows").mkdir()
    (root / ".github" / "workflows" / "ci.yml").write_text(
        "name: ci\n",
        encoding="utf-8",
    )
    (root / ".github" / "FUNDING.yml").write_text(
        "github: [demo]\n",
        encoding="utf-8",
    )
    return root


def test_authorization_fails_closed(tmp_path):
    root = make_repository(tmp_path)
    denied = authorization(root, explicitly_authorized=False)
    with pytest.raises(AuthorizationError):
        audit_repository(root, denied)


def test_authorization_repository_mismatch(tmp_path):
    root = make_repository(tmp_path)
    granted = authorization(root)
    other = tmp_path / "other"
    other.mkdir()
    with pytest.raises(AuthorizationError):
        audit_repository(other, granted)


def test_repository_audit_happy_path(tmp_path):
    root = make_repository(tmp_path)
    report = audit_repository(root, authorization(root))
    assert report.files_seen >= 7
    assert report.test_files >= 1
    assert report.workflow_files == 1
    assert report.has_license is True
    assert report.has_funding is True
    assert report.quality_score > 0.8
    assert len(report.report_hash) == 64
    assert "OAKGate" in render_markdown(report)


def test_repository_audit_finds_secret_without_exposing_value(tmp_path):
    root = make_repository(tmp_path)
    secret = "ghp_" + "A" * 30
    (root / "src" / "bad.py").write_text(
        f"TOKEN='{secret}'\n",
        encoding="utf-8",
    )
    report = audit_repository(root, authorization(root))
    assert report.privacy_summary["github_token"] == 1
    assert secret not in json.dumps(report.to_dict())
    assert any(finding.category == "privacy" for finding in report.findings)


def test_large_file_budget_is_explicit(tmp_path):
    root = make_repository(tmp_path)
    (root / "big.txt").write_text("x" * 100, encoding="utf-8")
    report = audit_repository(
        root,
        authorization(root),
        policy=AuditPolicy(max_text_file_bytes=10),
    )
    assert any(finding.category == "large_text_file" for finding in report.findings)


def test_oakgate_bundle_and_manifest(tmp_path):
    root = make_repository(tmp_path)
    output = tmp_path / "output"
    report, receipt = run_oakgate(root, authorization(root), output)
    assert (output / "audit-report.json").is_file()
    assert (output / "evidence-manifest.json").is_file()
    assert receipt.report_hash == report.report_hash
    assert receipt.files_in_bundle == 3
    assert receipt.external_actions == ()


def test_privacy_patterns_and_redaction():
    token = "sk-" + "x" * 25
    findings = scan_text(f"x={token}")
    assert findings and findings[0].severity == "critical"
    redacted, _ = redact_text(f"x={token}")
    assert token not in redacted
    with pytest.raises(SensitiveDataError):
        reject_secret_values({"note": token})
    with pytest.raises(SensitiveDataError):
        scan_payload({"account_number": "x"})


def test_merkle_proofs():
    leaves = [digest_payload({"i": index}) for index in range(9)]
    root = merkle_root(leaves)
    for index, leaf in enumerate(leaves):
        assert verify_merkle_proof(leaf, merkle_proof(leaves, index), root)
    assert not verify_merkle_proof(
        digest_payload({"bad": 1}),
        merkle_proof(leaves, 0),
        root,
    )


def test_manifest_is_deterministic(tmp_path):
    (tmp_path / "a").write_text("a", encoding="utf-8")
    (tmp_path / "b").write_text("b", encoding="utf-8")
    first = build_manifest(tmp_path, [tmp_path / "b", tmp_path / "a"])
    second = build_manifest(tmp_path, [tmp_path / "a", tmp_path / "b"])
    assert first.manifest_hash == second.manifest_hash
    assert first.merkle_root == second.merkle_root


def test_store_rejects_sensitive_payload_before_write(tmp_path):
    store = CampaignStore(tmp_path / "store.sqlite")
    with pytest.raises(SensitiveDataError):
        store.append_event("campaign", "event", {"account_number": "never"})


def test_store_upsert_and_iteration(tmp_path):
    store = CampaignStore(tmp_path / "store.sqlite")
    artifact = next(synthetic_artifacts(1))
    assessment = {"score": 0.5, "public_ready": True, "offer_ready": False}
    assert store.upsert_artifact(artifact, assessment) == "inserted"
    assert store.upsert_artifact(artifact, assessment) == "duplicate"
    assert store.count_artifacts() == 1
    assert next(store.iter_artifacts())["artifact_id"] == artifact["artifact_id"]


def test_campaign_50001_records_and_resume(tmp_path):
    store = CampaignStore(tmp_path / "campaign.sqlite")
    receipt = run_campaign(
        synthetic_artifacts(50_001),
        store,
        CampaignConfig(
            "C",
            checkpoint_every=5000,
            initial_batch_size=512,
        ),
    )
    assert receipt.seen == 50_001
    assert receipt.accepted == 50_001
    assert store.count_artifacts() == 50_001
    assert len(receipt.artifact_merkle_root) == 64
    resumed = run_campaign(
        synthetic_artifacts(50_001),
        store,
        CampaignConfig(
            "C",
            checkpoint_every=5000,
            initial_batch_size=512,
        ),
    )
    assert resumed.seen == 50_001


def test_campaign_stop_after_is_finite_run_budget(tmp_path):
    store = CampaignStore(tmp_path / "campaign.sqlite")
    receipt = run_campaign(
        synthetic_artifacts(1000),
        store,
        CampaignConfig("C", stop_after=123),
    )
    assert receipt.seen == 123
    assert receipt.source_exhausted is False


def test_campaign_quarantines_invalid_record(tmp_path):
    store = CampaignStore(tmp_path / "campaign.sqlite")
    records = [next(synthetic_artifacts(1)), {"bad": 1}]
    receipt = run_campaign(records, store, CampaignConfig("C"))
    assert receipt.accepted == 1
    assert receipt.quarantined == 1


def test_stable_shard():
    assert stable_shard("abc", 16) == stable_shard("abc", 16)
    with pytest.raises(ValueError):
        stable_shard("abc", 0)


def test_beta_posterior_and_funnel():
    estimate = posterior(2, 10)
    assert 0 < estimate.mean < 1
    assert estimate.interval_normal_approx()[0] >= 0
    snapshot = FunnelSnapshot(100, 20, 5, 1, 4, 2, 1, 0)
    result = analyze_funnel(snapshot)
    assert result["stages"]["click_to_sponsorship"]["observed_rate"] == 0.2
    action = recommend_funnel_action(snapshot)
    assert "measure" in action or "utility" in action


def test_funnel_invariants():
    with pytest.raises(ValueError):
        FunnelSnapshot(10, 20, 0, 0, 0, 0, 0, 0).validate()


def provider_event(
    event_id: str = "event",
    gross_minor: int = 100,
    fee_minor: int = 5,
) -> ProviderEvent:
    return ProviderEvent(
        "github_sponsors",
        event_id,
        gross_minor,
        fee_minor,
        "USD",
        "2026-08-03T00:00:00Z",
    )


def test_reconciliation_balanced_and_mismatch():
    balanced = reconcile_events([provider_event()], [provider_event()])
    assert balanced["balanced"] is True
    assert balanced["matched_net_minor_by_currency"] == {"USD": 95}
    mismatch = reconcile_events(
        [provider_event(gross_minor=100)],
        [provider_event(gross_minor=200)],
    )
    assert mismatch["balanced"] is False
    assert mismatch["mismatches"]


def test_reconciliation_duplicates():
    result = reconcile_events(
        [provider_event(), provider_event()],
        [provider_event()],
    )
    assert result["internal_duplicates"]


def test_pricing_envelope_and_economics():
    estimate = DeliveryEstimate(
        60,
        30,
        30,
        compute_minor=1000,
        tooling_minor=500,
    )
    envelope = price_envelope(estimate, hourly_cost_minor=6000)
    assert envelope.floor_minor < envelope.target_minor < envelope.ceiling_minor
    economics = delivery_economics(
        price_minor=envelope.target_minor,
        fee_minor=100,
        estimate=estimate,
        hourly_cost_minor=6000,
    )
    assert "contribution_minor" in economics
    assert "not net profit" in economics["non_claim"]


def candidate(identifier: str, **overrides) -> PortfolioCandidate:
    data = {
        "artifact_id": identifier,
        "evidence": 0.8,
        "utility": 0.8,
        "conversion": 0.6,
        "reuse": 0.8,
        "maintenance": 0.2,
        "risk": 0.2,
        "requested_minor": 1000,
        "dependencies": (),
    }
    data.update(overrides)
    return PortfolioCandidate(**data)


def test_pareto_and_dependency_allocation():
    base = candidate("BASE", requested_minor=500)
    child = candidate("CHILD", dependencies=("BASE",), requested_minor=500)
    weak = candidate(
        "WEAK",
        evidence=0.1,
        utility=0.1,
        conversion=0.1,
        reuse=0.1,
        maintenance=0.9,
        risk=0.9,
        requested_minor=2000,
    )
    assert weak not in pareto_front([base, child, weak])
    assert dependency_order([child, base]) == ["BASE", "CHILD"]
    allocation = allocate_portfolio([base, child], budget_minor=1000)
    assert [item["artifact_id"] for item in allocation] == ["BASE", "CHILD"]


def test_dependency_cycle():
    with pytest.raises(ValueError):
        dependency_order(
            [
                candidate("A", dependencies=("B",)),
                candidate("B", dependencies=("A",)),
            ]
        )


def sample_profile() -> SponsorProfile:
    return SponsorProfile(
        "demo",
        "Demo",
        "Mission",
        ("commit",),
        ("no guarantee",),
        (ProjectCard("Project", "Summary", "D", ("tests",), "pilot"),),
        (SponsorTier("Supporter", 500, "USD", 0, ("support",)),),
        "contact",
    )


def test_profile_bundle(tmp_path):
    profile = sample_profile()
    validation = validate_profile(profile)
    assert validation["valid"] is True
    bundle = write_profile_bundle(profile, tmp_path)
    assert Path(bundle["readme"]).is_file()
    assert "profile_hash" in bundle


def test_atlas_validation():
    atlas = default_system_atlas()
    assert len(atlas["nodes"]) >= 10
    assert len(atlas["atlas_hash"]) == 64
    with pytest.raises(ValueError):
        build_revenue_atlas(
            [AtlasNode("a", "kind", "label", "status", "evidence", True)],
            [AtlasEdge("edge", "a", "missing", "relation")],
        )
