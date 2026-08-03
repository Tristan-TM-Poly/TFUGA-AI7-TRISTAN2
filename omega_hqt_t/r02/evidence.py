from __future__ import annotations
from collections import defaultdict
from dataclasses import dataclass
from itertools import combinations
from statistics import mean
from typing import Any, Mapping, Sequence
from .foundations import (Claim, Contradiction, IngestReceipt, Observation, SecurityAssessment, Snapshot, SnapshotDiff, SourceDescriptor, merkle_root, sha256)


# --- provenance ---
@dataclass(frozen=True)
class ProvenanceBundle:
    bundle_id: str
    source_descriptors: Sequence[SourceDescriptor]
    receipts: Sequence[IngestReceipt]
    observation_count: int
    observation_merkle_root: str
    source_descriptor_merkle_root: str
    receipt_merkle_root: str
    claims: Mapping[str, bool]
    evidence_hash: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "bundle_id": self.bundle_id,
            "source_descriptors": [item.to_dict() for item in self.source_descriptors],
            "receipts": [item.to_dict() for item in self.receipts],
            "observation_count": self.observation_count,
            "observation_merkle_root": self.observation_merkle_root,
            "source_descriptor_merkle_root": self.source_descriptor_merkle_root,
            "receipt_merkle_root": self.receipt_merkle_root,
            "claims": dict(self.claims),
            "evidence_hash": self.evidence_hash,
        }

def build_provenance_bundle(
    sources: Sequence[SourceDescriptor],
    receipts: Sequence[IngestReceipt],
    observations: Sequence[Observation],
) -> ProvenanceBundle:
    payload = {
        "source_root": merkle_root(source.descriptor_hash for source in sources),
        "receipt_root": merkle_root(sha256(receipt.to_dict()) for receipt in receipts),
        "observation_root": merkle_root(observation.evidence_hash for observation in observations),
        "observation_count": len(observations),
    }
    evidence_hash = sha256(payload)
    return ProvenanceBundle(
        bundle_id=evidence_hash[:24],
        source_descriptors=tuple(sources),
        receipts=tuple(receipts),
        observation_count=len(observations),
        observation_merkle_root=payload["observation_root"],
        source_descriptor_merkle_root=payload["source_root"],
        receipt_merkle_root=payload["receipt_root"],
        claims={
            "raw_input_embedded": False,
            "content_hashes_retained": True,
            "licence_metadata_retained": True,
            "provenance_complete_for_fixture": True,
        },
        evidence_hash=evidence_hash,
    )


# --- temporal ---
def build_snapshot(
    observations: Sequence[Observation],
    created_at: str,
    parent_snapshot_id: str | None = None,
) -> Snapshot:
    ordered = sorted(observations, key=lambda item: (item.source_id, item.region_id, item.variable, item.observed_at, item.observation_id))
    payload = {
        "created_at": created_at,
        "parent": parent_snapshot_id,
        "observations": [item.observation_id for item in ordered],
        "root": merkle_root(item.evidence_hash for item in ordered),
    }
    evidence_hash = sha256(payload)
    return Snapshot(
        snapshot_id=evidence_hash[:24],
        created_at=created_at,
        source_ids=tuple(sorted({item.source_id for item in ordered})),
        observation_ids=tuple(item.observation_id for item in ordered),
        observation_merkle_root=payload["root"],
        parent_snapshot_id=parent_snapshot_id,
        status="VERSIONED_PUBLIC_EVIDENCE_FIXTURE",
        evidence_hash=evidence_hash,
    )

def diff_snapshots(
    before: Snapshot,
    after: Snapshot,
    before_observations: Sequence[Observation],
    after_observations: Sequence[Observation],
) -> SnapshotDiff:
    before_ids = set(before.observation_ids)
    after_ids = set(after.observation_ids)
    before_series = {(item.source_id, item.region_id, item.variable): item.evidence_hash for item in before_observations}
    after_series = {(item.source_id, item.region_id, item.variable): item.evidence_hash for item in after_observations}
    changed = sorted("|".join(key) for key in set(before_series) | set(after_series) if before_series.get(key) != after_series.get(key))
    payload = {
        "before": before.snapshot_id,
        "after": after.snapshot_id,
        "added": sorted(after_ids - before_ids),
        "removed": sorted(before_ids - after_ids),
        "unchanged": len(before_ids & after_ids),
        "changed_series": changed,
    }
    return SnapshotDiff(
        before_snapshot_id=before.snapshot_id,
        after_snapshot_id=after.snapshot_id,
        added_observation_ids=tuple(payload["added"]),
        removed_observation_ids=tuple(payload["removed"]),
        unchanged_count=payload["unchanged"],
        changed_series=tuple(changed),
        evidence_hash=sha256(payload),
    )

def group_series(observations: Sequence[Observation]) -> dict[str, list[Observation]]:
    grouped: dict[str, list[Observation]] = defaultdict(list)
    for observation in observations:
        series_id = f"{observation.source_id}|{observation.region_id}|{observation.variable}|{observation.unit}"
        grouped[series_id].append(observation)
    for values in grouped.values():
        values.sort(key=lambda item: item.observed_at)
    return dict(sorted(grouped.items()))


# --- claims ---
def compile_descriptive_claims(observations: Sequence[Observation]) -> tuple[Claim, ...]:
    claims: list[Claim] = []
    for series_id, series in group_series(observations).items():
        source_id, region_id, variable, unit = series_id.split("|", 3)
        average = mean(item.value for item in series)
        evidence_ids = tuple(item.observation_id for item in series)
        confidence = max(0.0, min(1.0, 1.0 - mean(item.uncertainty for item in series) / max(abs(average), 1.0)))
        statement = f"In the supplied fixture, mean {variable} for {region_id} is {average:.6g} {unit}."
        payload = {
            "series": series_id,
            "mean": average,
            "evidence": evidence_ids,
            "scope": "supplied_offline_fixture_only",
        }
        claims.append(Claim(
            claim_id=sha256(payload)[:24],
            statement=statement,
            subject=region_id,
            predicate=f"mean_{variable}",
            object_value=f"{average:.12g} {unit}",
            scope="supplied_offline_fixture_only",
            valid_from=series[0].observed_at,
            valid_to=series[-1].observed_at,
            status="DESCRIPTIVE_FIXTURE_CLAIM",
            confidence=confidence,
            evidence_ids=evidence_ids,
            counter_evidence_ids=(),
            assumptions=("records are correctly mapped", "fixture is not an operational grid replica"),
        ))
    return tuple(sorted(claims, key=lambda claim: claim.claim_id))

def claim_index(claims: Sequence[Claim]) -> dict[str, Claim]:
    return {claim.claim_id: claim for claim in claims}


# --- contradictions ---
def detect_claim_contradictions(claims: Sequence[Claim], relative_tolerance: float = 0.05) -> tuple[Contradiction, ...]:
    contradictions: list[Contradiction] = []
    for a, b in combinations(claims, 2):
        if (a.subject, a.predicate, a.valid_from, a.valid_to) != (b.subject, b.predicate, b.valid_from, b.valid_to):
            continue
        if a.object_value == b.object_value:
            continue
        def parse(value: str) -> float | None:
            try:
                return float(value.split()[0])
            except (ValueError, IndexError):
                return None
        av, bv = parse(a.object_value), parse(b.object_value)
        if av is None or bv is None:
            severity = 0.5
            kind = "SEMANTIC_CONFLICT"
        else:
            denominator = max(abs(av), abs(bv), 1.0)
            severity = min(1.0, abs(av - bv) / denominator)
            if severity <= relative_tolerance:
                continue
            kind = "NUMERIC_CONFLICT"
        payload = {"a": a.claim_id, "b": b.claim_id, "kind": kind, "severity": severity}
        contradictions.append(Contradiction(
            contradiction_id=sha256(payload)[:24],
            claim_a=a.claim_id,
            claim_b=b.claim_id,
            kind=kind,
            severity=severity,
            explanation="Claims share subject, predicate and validity window but disagree beyond tolerance.",
        ))
    return tuple(sorted(contradictions, key=lambda item: item.contradiction_id))


# --- security ---
def assess_composability_risk(
    sources: Sequence[SourceDescriptor],
    observations: Sequence[Observation],
) -> SecurityAssessment:
    if not observations:
        precision = linkage = density = specificity = 0.0
    else:
        region_count = len({item.region_id for item in observations})
        timestamp_count = len({item.observed_at for item in observations})
        variable_count = len({item.variable for item in observations})
        precision = min(1.0, 1.0 / max(region_count, 1) + 0.1 * variable_count)
        linkage = min(1.0, len(sources) / 5.0 + variable_count / 20.0)
        density = min(1.0, timestamp_count / 168.0)
        forbidden_hints = {"relay", "scada", "substation", "protection", "breaker", "credential", "command"}
        specificity_hits = sum(any(hint in item.variable.lower() for hint in forbidden_hints) for item in observations)
        specificity = min(1.0, specificity_hits / max(len(observations), 1) * 10.0)
    risk = round(0.25 * precision + 0.25 * linkage + 0.2 * density + 0.3 * specificity, 6)
    reasons: list[str] = []
    controls: list[str] = ["retain regional aggregation", "retain offline-only ingestion", "human review before publication"]
    if linkage >= 0.6:
        reasons.append("Multiple sources/variables increase linkage potential.")
        controls.append("perform mosaic-effect review")
    if density >= 0.5:
        reasons.append("Dense temporal observations may reveal behavioural patterns.")
        controls.append("coarsen timestamps before public export")
    if specificity > 0:
        reasons.append("Infrastructure-specific variable names detected.")
        controls.append("quarantine infrastructure-specific fields")
    if risk >= 0.7:
        decision = "BLOCK_PUBLICATION"
    elif risk >= 0.4:
        decision = "HUMAN_REVIEW_REQUIRED"
    else:
        decision = "PUBLIC_AGGREGATED_RESEARCH_ONLY"
    payload = {
        "sources": sorted(source.source_id for source in sources),
        "scores": [precision, linkage, density, specificity, risk],
        "decision": decision,
        "reasons": reasons,
        "controls": controls,
    }
    return SecurityAssessment(
        assessment_id=sha256(payload)[:24],
        source_ids=tuple(payload["sources"]),
        precision_score=round(precision, 6),
        linkage_score=round(linkage, 6),
        temporal_density_score=round(density, 6),
        infrastructure_specificity_score=round(specificity, 6),
        composability_risk=risk,
        decision=decision,
        reasons=tuple(reasons),
        controls=tuple(sorted(set(controls))),
    )
