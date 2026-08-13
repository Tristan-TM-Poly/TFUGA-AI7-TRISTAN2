from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any, Mapping

ALLOWED_SOURCE_STATES = frozenset({"CANON_MAIN", "HOLD_UPSTREAM", "MISSING"})
ALLOWED_VISIBILITY = frozenset({"public", "private"})


def _fingerprint(payload: Any) -> str:
    raw = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(raw).hexdigest()


def load_physicalization_manifest(path: str | Path) -> dict[str, Any]:
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    validate_physicalization_manifest(payload)
    return payload


def validate_physicalization_manifest(payload: Mapping[str, Any]) -> dict[str, Any]:
    errors: list[str] = []
    repos = list(payload.get("repositories", ()))
    names = [str(repo.get("name", "")) for repo in repos]
    if not repos:
        errors.append("manifest_requires_repositories")
    if len(names) != len(set(names)):
        errors.append("repository_names_must_be_unique")

    visibility_by_name = {str(repo.get("name", "")): str(repo.get("visibility", "")) for repo in repos}
    for repo in repos:
        name = str(repo.get("name", ""))
        visibility = str(repo.get("visibility", ""))
        if visibility not in ALLOWED_VISIBILITY:
            errors.append(f"{name}:invalid_visibility")
        for dep in repo.get("dependencies", ()):
            dep = str(dep)
            if dep not in visibility_by_name:
                errors.append(f"{name}:unknown_dependency:{dep}")
            elif visibility == "public" and visibility_by_name[dep] == "private":
                errors.append(f"{name}:public_must_not_depend_on_private:{dep}")

        bindings = list(repo.get("source_bindings", ()))
        if not bindings:
            errors.append(f"{name}:requires_source_bindings")
        for binding in bindings:
            capability = str(binding.get("capability", ""))
            state = str(binding.get("state", ""))
            if state not in ALLOWED_SOURCE_STATES:
                errors.append(f"{name}:{capability}:invalid_source_state")
            if state == "CANON_MAIN":
                if not binding.get("source_path"):
                    errors.append(f"{name}:{capability}:canon_main_requires_source_path")
                if not binding.get("source_sha"):
                    errors.append(f"{name}:{capability}:canon_main_requires_source_sha")
            else:
                if binding.get("materialize", False):
                    errors.append(f"{name}:{capability}:noncanonical_source_cannot_materialize")

    return {"status": "PASS" if not errors else "FAIL", "errors": errors, "repository_count": len(repos)}


def build_physicalization_plan(payload: Mapping[str, Any]) -> dict[str, Any]:
    validation = validate_physicalization_manifest(payload)
    if validation["status"] != "PASS":
        raise ValueError("; ".join(validation["errors"]))

    repositories: list[dict[str, Any]] = []
    for repo in payload.get("repositories", ()):
        ready = [dict(x) for x in repo.get("source_bindings", ()) if x.get("state") == "CANON_MAIN"]
        holds = [dict(x) for x in repo.get("source_bindings", ()) if x.get("state") != "CANON_MAIN"]
        declared = len(repo.get("source_bindings", ()))
        if holds:
            state = "PARTIAL_READY" if ready else "HOLD_FOR_SOURCE_CONVERGENCE"
        else:
            state = "READY_FOR_REVIEWED_PHYSICALIZATION"
        repositories.append({
            "name": repo["name"],
            "visibility": repo["visibility"],
            "dependencies": list(repo.get("dependencies", ())),
            "state": state,
            "declared_bindings": declared,
            "ready_bindings": ready,
            "holds": holds,
            "repository_creation_authorized": False,
        })

    plan = {
        "schema_version": "repo-physicalization-plan/v0.2",
        "source_repository": payload.get("source_repository"),
        "source_sha": payload.get("source_sha"),
        "repositories": repositories,
        "policy": {
            "current_main_sources_only": True,
            "public_to_private_dependency_forbidden": True,
            "repository_creation_authorized": False,
            "hold_is_not_failure": True,
        },
    }
    plan["fingerprint"] = _fingerprint(plan)
    return plan
