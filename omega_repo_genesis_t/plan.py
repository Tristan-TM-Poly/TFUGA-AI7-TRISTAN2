from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

from .model import Constellation


def load_constellation(path: str | Path) -> Constellation:
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    return Constellation.from_dict(payload)


def _fingerprint(payload: Any) -> str:
    raw = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(raw).hexdigest()


def build_plan(constellation: Constellation, *, threshold: float = 0.72) -> dict[str, Any]:
    candidates = []
    holds = []
    for repo in constellation.repositories:
        record = {
            "repository": f"{constellation.owner}/{repo.name}",
            "visibility": repo.visibility,
            "split_score": repo.split_score,
            "role": repo.role,
            "capabilities": list(repo.capabilities),
            "rationale": list(repo.split_rationale),
        }
        if repo.split_score >= threshold:
            candidates.append(record)
        else:
            record["hold_reason"] = "split_score_below_materialization_threshold"
            holds.append(record)

    plan = {
        "schema_version": "repo-genesis-plan/v0.1",
        "constellation_id": constellation.constellation_id,
        "source": {
            "repository": constellation.source_repository,
            "sha": constellation.source_sha,
            "prs": list(constellation.source_prs),
        },
        "policy": {
            "private_by_default": True,
            "public_creation_allowed": False,
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
    }
    plan["fingerprint"] = _fingerprint(plan)
    return plan


def bootstrap_files(repo: dict[str, Any], constellation: Constellation) -> dict[str, str]:
    spec = next(r for r in constellation.repositories if f"{constellation.owner}/{r.name}" == repo["repository"])
    genome = {
        "schema_version": "repo-genome/v0.1",
        "identity": spec.name,
        "role": spec.role,
        "visibility": "private",
        "source_repository": constellation.source_repository,
        "source_sha": constellation.source_sha,
        "source_prs": list(constellation.source_prs),
        "split_score": spec.split_score,
        "split_rationale": list(spec.split_rationale),
        "authority": {"default": "review", "automatic_merge": False, "public_release": False},
        "oak": {
            "claim_is_not_evidence": True,
            "ci_is_not_external_truth": True,
            "generation_is_not_authority": True,
        },
    }
    caps = {
        "schema_version": "capability-ir/v0.1",
        "provides": list(spec.capabilities),
        "consumes": list(spec.consumes),
        "produces": list(spec.produces),
    }
    relations = {"schema_version": "repo-relations/v0.1", "relations": list(spec.relations)}
    readme = f"""# {spec.name}

{spec.description}

## Role

`{spec.role}`

## Provenance

Generated as a private Ω-REPO-GENESIS-T∞ RepoCell from
`{constellation.source_repository}@{constellation.source_sha}`.

Historical source PRs: {", ".join("#"+str(x) for x in constellation.source_prs)}.

## OAK boundaries

- capability declaration != implementation proof
- repository creation != validated usefulness
- CI green != external scientific truth
- generated architecture != autonomous authority
- public release remains separately gated
"""
    workflow = """name: OAK Repo Cell

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
          assert genome["visibility"] == "private"
          assert genome["authority"]["automatic_merge"] is False
          assert genome["authority"]["public_release"] is False
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
