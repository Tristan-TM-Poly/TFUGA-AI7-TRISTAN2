from __future__ import annotations

import base64
import json
from dataclasses import dataclass
from typing import Any, Callable
from urllib.error import HTTPError
from urllib.request import Request, urlopen

from .model import Constellation
from .plan import bootstrap_files, build_plan

Transport = Callable[[str, str, dict[str, Any] | None], tuple[int, dict[str, Any]]]


def _default_transport(token: str) -> Transport:
    def call(method: str, url: str, payload: dict[str, Any] | None = None) -> tuple[int, dict[str, Any]]:
        data = None if payload is None else json.dumps(payload).encode()
        req = Request(url, method=method, data=data, headers={
            "Authorization": f"Bearer {token}",
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
            "Content-Type": "application/json",
            "User-Agent": "omega-repo-genesis-t/0.1",
        })
        try:
            with urlopen(req, timeout=30) as response:
                return response.status, json.loads(response.read().decode() or "{}")
        except HTTPError as exc:
            return exc.code, json.loads(exc.read().decode() or "{}")
    return call


@dataclass
class GitHubRepoFactory:
    token: str
    transport: Transport | None = None

    def __post_init__(self) -> None:
        if not self.token:
            raise ValueError("repository creation requires an explicit user-level GitHub token")
        if self.transport is None:
            self.transport = _default_transport(self.token)

    def _call(self, method: str, url: str, payload: dict[str, Any] | None = None) -> tuple[int, dict[str, Any]]:
        assert self.transport is not None
        return self.transport(method, url, payload)

    def exists(self, full_name: str) -> bool:
        status, _ = self._call("GET", f"https://api.github.com/repos/{full_name}")
        return status == 200

    def create_private_repository(self, owner: str, name: str, description: str) -> dict[str, Any]:
        if self.exists(f"{owner}/{name}"):
            return {"repository": f"{owner}/{name}", "status": "EXISTS", "mutated": False}
        status, payload = self._call("POST", "https://api.github.com/user/repos", {
            "name": name,
            "description": description,
            "private": True,
            "auto_init": True,
            "has_issues": True,
            "has_projects": False,
            "has_wiki": False,
            "delete_branch_on_merge": True,
        })
        if status != 201:
            raise RuntimeError(f"GitHub repository creation failed HTTP {status}: {payload}")
        actual_owner = payload.get("owner", {}).get("login")
        if actual_owner and actual_owner != owner:
            raise RuntimeError(f"created repository owner mismatch: expected {owner}, got {actual_owner}")
        return {"repository": f"{owner}/{name}", "status": "CREATED_PRIVATE", "mutated": True}

    def put_file_if_absent(self, full_name: str, path: str, content: str) -> dict[str, Any]:
        status, _ = self._call("GET", f"https://api.github.com/repos/{full_name}/contents/{path}")
        if status == 200:
            return {"path": path, "status": "EXISTS", "mutated": False}
        encoded = base64.b64encode(content.encode()).decode()
        status, payload = self._call("PUT", f"https://api.github.com/repos/{full_name}/contents/{path}", {
            "message": f"bootstrap(repo-cell): add {path}",
            "content": encoded,
        })
        if status != 201:
            raise RuntimeError(f"GitHub bootstrap failed for {full_name}/{path}: HTTP {status}: {payload}")
        return {"path": path, "status": "CREATED", "mutated": True}

    def materialize(self, constellation: Constellation, *, threshold: float = 0.72) -> dict[str, Any]:
        plan = build_plan(constellation, threshold=threshold)
        results = []
        for candidate in plan["create_candidates"]:
            full_name = candidate["repository"]
            owner, name = full_name.split("/", 1)
            spec = next(r for r in constellation.repositories if r.name == name)
            repo_result = self.create_private_repository(owner, name, spec.description)
            file_results = [
                self.put_file_if_absent(full_name, path, content)
                for path, content in bootstrap_files(candidate, constellation).items()
            ]
            results.append({"repository": full_name, "repo": repo_result, "files": file_results})
        return {
            "schema_version": "repo-genesis-receipt/v0.1",
            "constellation_id": constellation.constellation_id,
            "private_only": True,
            "destructive_updates": False,
            "results": results,
        }
