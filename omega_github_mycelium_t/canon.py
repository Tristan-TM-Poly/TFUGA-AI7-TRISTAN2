from __future__ import annotations

from typing import Iterable

from .models import ArtifactSpec, CampaignPlan, CreationRecord, OAKFinding, FindingSeverity


class CanonSynchronizer:
    """Generate a review-only canon update proposal after a campaign."""

    def propose(
        self,
        creation: CreationRecord,
        campaign: CampaignPlan,
        artifacts: Iterable[ArtifactSpec],
        findings: Iterable[OAKFinding],
    ) -> dict[str, object]:
        artifacts = tuple(artifacts)
        findings = tuple(findings)
        blocked = any(finding.severity is FindingSeverity.BLOCKER for finding in findings)
        return {
            "creation_id": creation.creation_id,
            "campaign_id": campaign.campaign_id,
            "proposal_status": "blocked" if blocked else "ready_for_human_review",
            "automatic_canon_update_performed": False,
            "proposed_updates": [
                {
                    "path": creation.canonical_path,
                    "action": "update_status_after_verified_merge",
                    "condition": "exact reviewed head merged and evidence bundle audited",
                },
                {
                    "path": "generated/omega_github_mycelium_t/m_plus.jsonl",
                    "action": "append_validated_patterns_only",
                    "condition": "tests and claims independently reviewed",
                },
                {
                    "path": "generated/omega_github_mycelium_t/m_minus.jsonl",
                    "action": "append_failures_and_limitations",
                    "condition": "always preserve negative outcomes",
                },
            ],
            "artifact_kinds": sorted({artifact.kind for artifact in artifacts}),
            "next_proof": "Implement one bounded artifact, compare it to a baseline and bind the result to an exact commit.",
            "human_review_required": True,
        }
