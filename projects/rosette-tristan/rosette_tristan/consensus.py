from __future__ import annotations

from collections import Counter, defaultdict
from dataclasses import asdict, dataclass, field
import re


@dataclass(frozen=True)
class ArtifactVote:
    artifact_type: str
    value: str
    extractor: str
    weight: float = 1.0
    confidence: float = 0.5
    note: str = ""


@dataclass
class ConsensusArtifact:
    artifact_id: str
    artifact_type: str
    consensus_value: str
    votes: list[ArtifactVote]
    confidence_tensor: dict[str, float]
    oak_status: str
    required_next_check: list[str] = field(default_factory=list)
    conflicts: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        data = asdict(self)
        data["votes"] = [asdict(vote) for vote in self.votes]
        return data


def normalize_latex(value: str) -> str:
    value = value.strip()
    value = re.sub(r"\s+", "", value)
    value = value.replace("\\left", "").replace("\\right", "")
    return value


def build_consensus(votes: list[ArtifactVote], artifact_id: str = "A1") -> ConsensusArtifact:
    if not votes:
        return ConsensusArtifact(
            artifact_id=artifact_id,
            artifact_type="unknown",
            consensus_value="",
            votes=[],
            confidence_tensor={"text": 0.0, "layout": 0.0, "math": 0.0, "theory": 0.0},
            oak_status="failed_no_votes",
            required_next_check=["rerun_extractors"],
            conflicts=[],
        )

    by_norm: dict[str, list[ArtifactVote]] = defaultdict(list)
    original_for_norm: dict[str, str] = {}
    for vote in votes:
        key = normalize_latex(vote.value) if vote.artifact_type == "equation" else vote.value.strip().lower()
        by_norm[key].append(vote)
        original_for_norm.setdefault(key, vote.value.strip())

    def support_score(item: tuple[str, list[ArtifactVote]]) -> float:
        _, group = item
        return sum(max(0.0, vote.weight) * max(0.0, vote.confidence) for vote in group)

    best_key, best_group = max(by_norm.items(), key=support_score)
    total_support = sum(support_score((key, group)) for key, group in by_norm.items()) or 1.0
    best_support = support_score((best_key, best_group))
    agreement = best_support / total_support

    extractor_counts = Counter(vote.extractor for vote in votes)
    conflicts = []
    if len(by_norm) > 1:
        conflicts.append(f"{len(by_norm)} distinct readings across {len(votes)} votes")
    missing = [name for name, count in extractor_counts.items() if count == 0]
    conflicts.extend(f"missing vote: {name}" for name in missing)

    artifact_type = best_group[0].artifact_type
    math_conf = agreement if artifact_type == "equation" else 0.0
    theory_conf = min(0.75, agreement)
    oak_status = "usable_not_certified" if agreement >= 0.6 else "conflicted_uncertain"
    required = ["source_ref_check", "oak_review"]
    if artifact_type == "equation":
        required.extend(["render_diff_repair", "dimensional_oak"])
    if artifact_type == "claim":
        required.append("claim_evidence_graph")

    return ConsensusArtifact(
        artifact_id=artifact_id,
        artifact_type=artifact_type,
        consensus_value=original_for_norm[best_key],
        votes=votes,
        confidence_tensor={
            "text": round(agreement, 4),
            "layout": 0.5,
            "math": round(math_conf, 4),
            "theory": round(theory_conf, 4),
        },
        oak_status=oak_status,
        required_next_check=required,
        conflicts=conflicts,
    )
