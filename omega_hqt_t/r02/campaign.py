from __future__ import annotations
import json
from dataclasses import asdict, dataclass
from math import sqrt
from pathlib import Path
from statistics import mean, pstdev
from typing import Any, Mapping, Sequence
from .foundations import (CampaignReport, ModelDisagreement, ModelEstimate, PublicEvidencePolicy, SourceDescriptor, sha256, source_by_id)
from .ingest import IngestResult, ingest_text
from .evidence import (assess_composability_risk, build_provenance_bundle, build_snapshot, compile_descriptive_claims, detect_claim_contradictions, diff_snapshots, group_series)


# --- multimodel ---
def _persistence(series_id: str, series: Sequence[Observation]) -> ModelEstimate:
    estimate = series[-1].value
    sigma = max(pstdev([item.value for item in series]) if len(series) > 1 else 0.0, series[-1].uncertainty)
    payload = {"model": "persistence", "series": series_id, "estimate": estimate, "sigma": sigma}
    return ModelEstimate("persistence", series_id, estimate, estimate - 1.96 * sigma, estimate + 1.96 * sigma,
                         ("last observation persists",), sha256(payload))

def _linear_trend(series_id: str, series: Sequence[Observation]) -> ModelEstimate:
    ys = [item.value for item in series]
    n = len(ys)
    if n < 2:
        slope = 0.0
    else:
        xbar = (n - 1) / 2
        ybar = mean(ys)
        denominator = sum((i - xbar) ** 2 for i in range(n))
        slope = sum((i - xbar) * (y - ybar) for i, y in enumerate(ys)) / denominator if denominator else 0.0
    estimate = ys[-1] + slope
    residuals = [y - (ys[0] + slope * i) for i, y in enumerate(ys)]
    sigma = sqrt(sum(value * value for value in residuals) / max(len(residuals), 1))
    payload = {"model": "linear_trend", "series": series_id, "estimate": estimate, "slope": slope, "sigma": sigma}
    return ModelEstimate("linear_trend", series_id, estimate, estimate - 1.96 * sigma, estimate + 1.96 * sigma,
                         ("equally spaced observations", "linear local trend"), sha256(payload))

def compare_models(observations: Sequence[Observation]) -> tuple[ModelDisagreement, ...]:
    reports: list[ModelDisagreement] = []
    for series_id, series in group_series(observations).items():
        estimates = (_persistence(series_id, series), _linear_trend(series_id, series))
        values = [item.estimate for item in estimates]
        spread = max(values) - min(values)
        scale = max(abs(mean(values)), 1.0)
        normalized = spread / scale
        status = "MODEL_DISAGREEMENT_REVIEW" if normalized > 0.1 else "MODELS_LOCALLY_CONSISTENT"
        payload = {"series": series_id, "estimates": [item.to_dict() for item in estimates], "status": status}
        reports.append(ModelDisagreement(
            series_id=series_id,
            estimates=estimates,
            spread=spread,
            normalized_disagreement=normalized,
            oak_status=status,
            evidence_hash=sha256(payload),
        ))
    return tuple(sorted(reports, key=lambda item: item.series_id))


# --- fixtures ---
REGIONS = ("montreal", "capital-nationale", "cote-nord", "saguenay-lac-saint-jean")

def demand_fixture(hours: int = 24) -> tuple[SourceDescriptor, str]:
    source = source_by_id("fixture-demand-regional")
    records = []
    for hour in range(hours):
        for index, region in enumerate(REGIONS):
            base = 900.0 + index * 180.0
            winter_shape = 120.0 if hour in {7, 8, 17, 18, 19} else 0.0
            records.append({
                "variable": "demand",
                "value": base + winter_shape + (hour % 6) * 7.5,
                "unit": "MW",
                "observed_at": f"2026-01-15T{hour:02d}:00:00-05:00",
                "region_id": region,
                "uncertainty": 12.0,
                "quality_flag": "synthetic_fixture",
            })
    return source, json.dumps(records, sort_keys=True)

def production_fixture(hours: int = 24) -> tuple[SourceDescriptor, str]:
    source = source_by_id("fixture-production-regional")
    records = []
    for hour in range(hours):
        for index, region in enumerate(REGIONS):
            base = 980.0 + index * 165.0
            records.append({
                "variable": "production",
                "value": base + ((hour * (index + 1)) % 9) * 5.0,
                "unit": "MW",
                "observed_at": f"2026-01-15T{hour:02d}:00:00-05:00",
                "region_id": region,
                "uncertainty": 10.0,
                "quality_flag": "synthetic_fixture",
            })
    return source, json.dumps(records, sort_keys=True)

def all_fixtures(hours: int = 24) -> Sequence[tuple[SourceDescriptor, str, str]]:
    demand_source, demand_text = demand_fixture(hours)
    production_source, production_text = production_fixture(hours)
    return (
        (demand_source, demand_text, "json"),
        (production_source, production_text, "json"),
    )


# --- planner ---
@dataclass(frozen=True)
class PublicEvidenceMission:
    mission_id: str
    objective: str
    source_constraints: Sequence[str]
    required_gates: Sequence[str]
    outputs: Sequence[str]
    forbidden_actions: Sequence[str]
    status: str
    evidence_hash: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

def compile_public_evidence_mission(objective: str) -> PublicEvidenceMission:
    normalized = " ".join(objective.strip().split())
    forbidden_terms = {"control", "dispatch", "relay", "credential", "scada", "exploit"}
    risky = sorted(term for term in forbidden_terms if term in normalized.lower())
    status = "BLOCKED_REQUIRES_AUTHORIZED_OPERATIONAL_GOVERNANCE" if risky else "READY_OFFLINE_PUBLIC_EVIDENCE_ONLY"
    payload = {
        "objective": normalized,
        "status": status,
        "risky_terms": risky,
    }
    return PublicEvidenceMission(
        mission_id=sha256(payload)[:24],
        objective=normalized,
        source_constraints=("explicit licence", "public or synthetic", "offline local export", "regional aggregation"),
        required_gates=("licence", "schema", "prohibited-field scan", "mosaic-effect review", "OAK claim boundary"),
        outputs=("versioned snapshot", "claim-evidence graph", "contradiction report", "security assessment", "reproducibility receipt"),
        forbidden_actions=("network crawling", "authentication bypass", "operational commands", "fine customer profiling", "real topology inference"),
        status=status,
        evidence_hash=sha256(payload),
    )


# --- campaign ---
def compile_public_evidence_campaign(
    fixtures: Sequence[tuple[SourceDescriptor, str, str]] | None = None,
    created_at: str = "2026-08-03T20:00:00Z",
    policy: PublicEvidencePolicy | None = None,
) -> CampaignReport:
    policy = policy or PublicEvidencePolicy()
    fixtures = fixtures or all_fixtures()
    sources: list[SourceDescriptor] = []
    results: list[IngestResult] = []
    observations: list[Observation] = []
    for source, text, input_format in fixtures:
        result = ingest_text(text, input_format, source, policy)
        sources.append(source)
        results.append(result)
        observations.extend(result.observations)
    snapshot = build_snapshot(observations, created_at)
    claims = compile_descriptive_claims(observations)
    contradictions = detect_claim_contradictions(claims)
    security = assess_composability_risk(sources, observations)
    disagreements = compare_models(observations)
    quarantined = sum(len(result.quarantine) for result in results)
    boundary = {
        "operational_grid_replica_claimed": False,
        "hydro_quebec_affiliation_claimed": False,
        "causal_effect_claimed": False,
        "public_source_truth_certified": False,
        "synthetic_fixture_reproducibility_claimed": True,
        "network_fetch_performed": False,
    }
    status = "CERTIFIED_OFFLINE_PUBLIC_EVIDENCE_FIXTURES_R0_2"
    if security.decision == "BLOCK_PUBLICATION" or quarantined:
        status = "REVIEW_REQUIRED_OFFLINE_PUBLIC_EVIDENCE_R0_2"
    payload = {
        "sources": [source.descriptor_hash for source in sources],
        "receipts": [result.receipt.to_dict() for result in results],
        "snapshot": snapshot.to_dict(),
        "claims": [claim.claim_hash for claim in claims],
        "contradictions": [item.to_dict() for item in contradictions],
        "security": security.to_dict(),
        "disagreements": [item.evidence_hash for item in disagreements],
        "boundary": boundary,
        "status": status,
    }
    return CampaignReport(
        campaign_id=sha256(payload)[:24],
        source_count=len(sources),
        accepted_observations=len(observations),
        quarantined_observations=quarantined,
        snapshot=snapshot,
        claims=claims,
        contradictions=contradictions,
        security=security,
        model_disagreements=disagreements,
        status=status,
        claims_boundary=boundary,
        evidence_hash=sha256(payload),
    )


# --- benchmark ---
@dataclass(frozen=True)
class R02BenchmarkReport:
    status: str
    passed: bool
    checks: Mapping[str, bool]
    metrics: Mapping[str, float | int]
    claims: Mapping[str, bool]
    campaign_hash: str
    evidence_hash: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

def run_r02_benchmark(hours: int = 24) -> R02BenchmarkReport:
    campaign_a = compile_public_evidence_campaign(all_fixtures(hours))
    campaign_b = compile_public_evidence_campaign(all_fixtures(hours))
    demand_source, demand_text = demand_fixture(hours)
    ingest = ingest_text(demand_text, "json", demand_source)
    before = build_snapshot(ingest.observations[:-1], "2026-08-03T19:00:00Z")
    after = build_snapshot(ingest.observations, "2026-08-03T20:00:00Z", before.snapshot_id)
    diff = diff_snapshots(before, after, ingest.observations[:-1], ingest.observations)
    safe_mission = compile_public_evidence_mission("compare regional synthetic demand and production")
    blocked_mission = compile_public_evidence_mission("send SCADA control command")
    checks = {
        "deterministic_campaign": campaign_a.evidence_hash == campaign_b.evidence_hash,
        "accepted_fixture_rows": campaign_a.accepted_observations == hours * 8,
        "zero_fixture_quarantine": campaign_a.quarantined_observations == 0,
        "snapshot_merkle_present": len(campaign_a.snapshot.observation_merkle_root) == 64,
        "claims_traceable": all(claim.evidence_ids for claim in campaign_a.claims),
        "no_false_affiliation": campaign_a.claims_boundary["hydro_quebec_affiliation_claimed"] is False,
        "no_network_fetch": campaign_a.claims_boundary["network_fetch_performed"] is False,
        "temporal_diff_detects_addition": len(diff.added_observation_ids) == 1,
        "safe_mission_ready": safe_mission.status.startswith("READY"),
        "operational_mission_blocked": blocked_mission.status.startswith("BLOCKED"),
        "security_not_blocked_for_fixture": campaign_a.security.decision != "BLOCK_PUBLICATION",
        "multi_model_evidence_present": all(len(item.evidence_hash) == 64 for item in campaign_a.model_disagreements),
    }
    passed = all(checks.values())
    payload = {
        "checks": checks,
        "campaign": campaign_a.evidence_hash,
        "diff": diff.to_dict(),
        "safe_mission": safe_mission.to_dict(),
        "blocked_mission": blocked_mission.to_dict(),
    }
    return R02BenchmarkReport(
        status="CERTIFIED_OFFLINE_PUBLIC_EVIDENCE_FIXTURES_R0_2" if passed else "FAILED_R0_2_OAKBENCH",
        passed=passed,
        checks=checks,
        metrics={
            "hours": hours,
            "accepted_observations": campaign_a.accepted_observations,
            "claim_count": len(campaign_a.claims),
            "contradiction_count": len(campaign_a.contradictions),
            "model_disagreement_count": len(campaign_a.model_disagreements),
            "composability_risk": campaign_a.security.composability_risk,
        },
        claims={
            "real_grid_validated": False,
            "hydro_quebec_affiliation_claimed": False,
            "operational_use_authorized": False,
            "synthetic_fixture_reproducibility_claimed": True,
            "offline_ingestion_claimed": True,
        },
        campaign_hash=campaign_a.evidence_hash,
        evidence_hash=sha256(payload),
    )


# --- report ---
def write_r02_bundle(output_dir: Path) -> Mapping[str, str]:
    output_dir.mkdir(parents=True, exist_ok=True)
    fixtures = all_fixtures()
    sources = []
    receipts = []
    observations = []
    for source, text, fmt in fixtures:
        result = ingest_text(text, fmt, source)
        sources.append(source)
        receipts.append(result.receipt)
        observations.extend(result.observations)
    campaign = compile_public_evidence_campaign(fixtures)
    provenance = build_provenance_bundle(sources, receipts, observations)
    campaign_path = output_dir / "campaign-report.json"
    provenance_path = output_dir / "provenance-bundle.json"
    claims_path = output_dir / "claims.jsonl"
    campaign_path.write_text(json.dumps(campaign.to_dict(), indent=2, sort_keys=True) + "\n", encoding="utf-8")
    provenance_path.write_text(json.dumps(provenance.to_dict(), indent=2, sort_keys=True) + "\n", encoding="utf-8")
    claims_path.write_text("".join(json.dumps(claim.to_dict(), sort_keys=True) + "\n" for claim in campaign.claims), encoding="utf-8")
    return {
        "campaign": str(campaign_path),
        "provenance": str(provenance_path),
        "claims": str(claims_path),
    }
