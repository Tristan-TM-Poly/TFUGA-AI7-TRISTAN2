from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .model import Constellation, RepoSpec

PUBLIC_DRIVERS = frozenset({
    "protocol",
    "kernel",
    "benchmark",
    "documentation",
    "conformance",
    "public_evidence",
})
PRIVATE_BLOCKERS = frozenset({
    "secrets",
    "personal_data",
    "customer_data",
    "unpublished_ip",
    "restricted_third_party_data",
    "privileged_authority",
})


@dataclass(frozen=True)
class VisibilityDecision:
    declared_visibility: str
    allowed: bool
    decision: str
    reasons: tuple[str, ...]

    def to_dict(self) -> dict[str, object]:
        return {
            "declared_visibility": self.declared_visibility,
            "allowed": self.allowed,
            "decision": self.decision,
            "reasons": list(self.reasons),
        }


def evaluate_visibility(spec: RepoSpec) -> VisibilityDecision:
    if spec.visibility == "private":
        return VisibilityDecision("private", True, "PRIVATE", ("private_by_default",))

    unknown_drivers = sorted(set(spec.public_drivers) - PUBLIC_DRIVERS)
    unknown_blockers = sorted(set(spec.private_blockers) - PRIVATE_BLOCKERS)
    reasons: list[str] = []
    if unknown_drivers:
        reasons.append("unknown_public_driver:" + ",".join(unknown_drivers))
    if unknown_blockers:
        reasons.append("unknown_private_blocker:" + ",".join(unknown_blockers))
    if spec.private_blockers:
        reasons.append("private_blocker_present:" + ",".join(sorted(spec.private_blockers)))
    if not spec.public_drivers:
        reasons.append("public_repo_requires_explicit_public_driver")

    if reasons:
        return VisibilityDecision("public", False, "HOLD", tuple(reasons))
    return VisibilityDecision("public", True, "PUBLIC", ("public_surface_gate_passed",))


def load_constellation(path: str | Path) -> Constellation:
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    return Constellation.from_dict(payload)


def _fingerprint(payload: Any) -> str:
    raw = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(raw).hexdigest()


def build_plan(constellation: Constellation, *, threshold: float = 0.72) -> dict[str, Any]:
    candidates = []
    holds = []
    public_candidates = 0
    private_candidates = 0
    for repo in constellation.repositories:
        gate = evaluate_visibility(repo)
        record = {
            "repository": f"{constellation.owner}/{repo.name}",
            "visibility": repo.visibility,
            "visibility_gate": gate.to_dict(),
            "split_score": repo.split_score,
            "role": repo.role,
            "capabilities": list(repo.capabilities),
            "rationale": list(repo.split_rationale),
        }
        if repo.split_score < threshold:
            record["hold_reason"] = "split_score_below_materialization_threshold"
            holds.append(record)
        elif not gate.allowed:
            record["hold_reason"] = "visibility_gate_failed"
            holds.append(record)
        else:
            candidates.append(record)
            if repo.visibility == "public":
                public_candidates += 1
            else:
                private_candidates += 1

    plan = {
        "schema_version": "repo-genesis-plan/v0.2",
        "constellation_id": constellation.constellation_id,
        "source": {
            "repository": constellation.source_repository,
            "sha": constellation.source_sha,
            "prs": list(constellation.source_prs),
        },
        "policy": {
            "private_by_default": True,
            "public_creation_allowed": public_candidates > 0,
            "public_requires_visibility_gate": True,
            "public_materialization_requires_explicit_allow_public": True,
            "destructive_updates_allowed": False,
            "overwrite_existing_files": False,
            "materialization_threshold": threshold,
        },
        "create_candidates": candidates,
        "holds": holds,
        "counts": {
            "declared": len(constellation.repositories),
            "create_candidates": len(candidates),
            "holds": len(holds),
        },
        "visibility_counts": {
            "public_candidates": public_candidates,
            "private_candidates": private_candidates,
            "public_holds": sum(1 for r in holds if r["visibility"] == "public"),
            "private_holds": sum(1 for r in holds if r["visibility"] == "private"),
        },
    }
    plan["fingerprint"] = _fingerprint(plan)
    return plan


def bootstrap_files(repo: dict[str, Any], constellation: Constellation) -> dict[str, str]:
    spec = next(r for r in constellation.repositories if f"{constellation.owner}/{r.name}" == repo["repository"])
    gate = evaluate_visibility(spec)
    if not gate.allowed:
        raise ValueError(f"visibility gate is HOLD for {spec.name}: {gate.reasons}")

    genome = {
        "schema_version": "repo-genome/v0.2",
        "identity": spec.name,
        "role": spec.role,
        "visibility": spec.visibility,
        "visibility_gate": gate.to_dict(),
        "source_repository": constellation.source_repository,
        "source_sha": constellation.source_sha,
        "source_prs": list(constellation.source_prs),
        "split_score": spec.split_score,
        "split_rationale": list(spec.split_rationale),
        "authority": {
            "default": "review",
            "automatic_merge": False,
            "automatic_publication": False,
            "public_release_requires_review": True,
        },
        "oak": {
            "claim_is_not_evidence": True,
            "ci_is_not_external_truth": True,
            "generation_is_not_authority": True,
            "public_visibility_is_not_ip_clearance": True,
        },
    }
    caps = {
        "schema_version": "capability-ir/v0.2",
        "provides": list(spec.capabilities),
        "consumes": list(spec.consumes),
        "produces": list(spec.produces),
    }
    relations = {"schema_version": "repo-relations/v0.2", "relations": list(spec.relations)}
    readme = f"""# {spec.name}

{spec.description}

## Role

`{spec.role}`

## Target visibility

`{spec.visibility}`

## Provenance

Generated as an Ω-REPO-GENESIS-T∞ RepoCell candidate from
`{constellation.source_repository}@{constellation.source_sha}`.

Historical source PRs: {", ".join("#"+str(x) for x in constellation.source_prs)}.

## OAK boundaries

- capability declaration != implementation proof
- repository creation != validated usefulness
- CI green != external scientific truth
- generated architecture != autonomous authority
- public visibility != IP/legal/privacy clearance
- publication remains separately reviewed even when target visibility is public
"""
    workflow = f"""name: OAK Repo Cell

on:
  pull_request:
  workflow_dispatch:

permissions:
  contents: read

jobs:
  repo-cell-contract:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.12"
      - name: Validate machine contracts
        run: |
          python - <<'PY'
          import json
          from pathlib import Path
          for path in ["repo.genome.json", "capabilities.json", "relations.json"]:
              payload = json.loads(Path(path).read_text())
              assert "schema_version" in payload, path
          genome = json.loads(Path("repo.genome.json").read_text())
          assert genome["visibility"] in {{"private", "public"}}
          assert genome["visibility"] == "{spec.visibility}"
          assert genome["authority"]["automatic_merge"] is False
          assert genome["authority"]["automatic_publication"] is False
          assert genome["authority"]["public_release_requires_review"] is True
          assert genome["visibility_gate"]["allowed"] is True
          print("OAK repo-cell contract: PASS")
          PY
"""
    return {
        "README.md": readme,
        "repo.genome.json": json.dumps(genome, indent=2, sort_keys=True) + "\n",
        "capabilities.json": json.dumps(caps, indent=2, sort_keys=True) + "\n",
        "relations.json": json.dumps(relations, indent=2, sort_keys=True) + "\n",
        ".github/workflows/oak-repo-cell.yml": workflow,
    }
