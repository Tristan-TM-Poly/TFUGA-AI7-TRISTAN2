"""R1 cross-repository WorkGraph and immutable capability routing."""
from __future__ import annotations
from dataclasses import asdict, dataclass
import argparse
import hashlib
import json
from pathlib import Path
import re
from typing import Any, Iterable

_SHA_RE = re.compile(r"^[0-9a-f]{40}$")
_TOKEN_RE = re.compile(r"[a-z0-9]+")

def _tokens(value: str) -> set[str]:
    return set(_TOKEN_RE.findall(str(value).lower()))

@dataclass(frozen=True)
class RepoSnapshot:
    repository: str
    head_sha: str
    default_branch: str = "main"
    ref: str = "main"
    visibility: str = "public"
    authority: str = "READ_PLAN"

    def __post_init__(self) -> None:
        if "/" not in self.repository or self.repository.startswith("/") or self.repository.endswith("/"):
            raise ValueError("repository must be owner/name")
        if not _SHA_RE.fullmatch(self.head_sha):
            raise ValueError("head_sha must be an exact 40-character lowercase SHA")
        if not self.default_branch.strip() or not self.ref.strip():
            raise ValueError("default_branch and ref cannot be empty")
        if self.visibility not in {"public", "private", "internal"}:
            raise ValueError("unsupported visibility")
        if self.authority not in {"DISCOVER", "READ", "READ_PLAN", "DRAFT_WRITE"}:
            raise ValueError("unsupported authority")

    @property
    def identity(self) -> str:
        return f"{self.repository}@{self.head_sha}"

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["identity"] = self.identity
        return payload

@dataclass(frozen=True)
class CrossRepoCapability:
    capability_id: str
    repository: str
    head_sha: str
    name: str
    domains: tuple[str, ...] = ()
    evidence_weight: float = 0.0
    maturity: str = "DECLARED"
    read_only: bool = True
    depends_on: tuple[str, ...] = ()
    limitations: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if not self.capability_id.strip():
            raise ValueError("capability_id required")
        if not _SHA_RE.fullmatch(self.head_sha):
            raise ValueError("capability head_sha must be exact")
        if not 0.0 <= float(self.evidence_weight) <= 1.0:
            raise ValueError("evidence_weight must be between 0 and 1")
        object.__setattr__(self, "domains", tuple(dict.fromkeys(self.domains)))
        object.__setattr__(self, "depends_on", tuple(dict.fromkeys(self.depends_on)))
        object.__setattr__(self, "limitations", tuple(dict.fromkeys(self.limitations)))

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> "CrossRepoCapability":
        data = dict(payload)
        for field in ("domains", "depends_on", "limitations"):
            data[field] = tuple(data.get(field, ()))
        return cls(**data)

@dataclass(frozen=True)
class CrossRepoMatch:
    capability_id: str
    repository_identity: str
    score: float
    evidence_weight: float
    maturity: str
    read_only: bool
    content_disclosure: str
    status: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

class CrossRepoRegistry:
    def __init__(self, repositories: Iterable[RepoSnapshot], capabilities: Iterable[CrossRepoCapability]):
        repo_list = tuple(repositories)
        self.repositories = {repo.repository: repo for repo in repo_list}
        if len(self.repositories) != len(repo_list):
            raise ValueError("duplicate repository snapshot")
        self.capabilities: dict[str, CrossRepoCapability] = {}
        for capability in capabilities:
            if capability.capability_id in self.capabilities:
                raise ValueError(f"duplicate capability_id: {capability.capability_id}")
            repo = self.repositories.get(capability.repository)
            if repo is None:
                raise ValueError(f"capability references unknown repository: {capability.repository}")
            if capability.head_sha != repo.head_sha:
                raise ValueError(
                    f"stale capability binding: {capability.capability_id} uses {capability.head_sha}, snapshot is {repo.head_sha}"
                )
            self.capabilities[capability.capability_id] = capability
        self._validate_dependencies()

    def _validate_dependencies(self) -> None:
        for capability in self.capabilities.values():
            for dependency in capability.depends_on:
                if dependency not in self.capabilities:
                    raise ValueError(f"missing capability dependency: {capability.capability_id}->{dependency}")
        visiting: set[str] = set()
        visited: set[str] = set()
        def visit(capability_id: str) -> None:
            if capability_id in visited:
                return
            if capability_id in visiting:
                raise ValueError("cross-repository capability dependency cycle")
            visiting.add(capability_id)
            for dependency in self.capabilities[capability_id].depends_on:
                visit(dependency)
            visiting.remove(capability_id)
            visited.add(capability_id)
        for capability_id in sorted(self.capabilities):
            visit(capability_id)

    def dependency_closure(self, capability_id: str) -> tuple[str, ...]:
        if capability_id not in self.capabilities:
            raise KeyError(capability_id)
        output: list[str] = []
        seen: set[str] = set()
        def walk(current: str) -> None:
            for dependency in self.capabilities[current].depends_on:
                if dependency not in seen:
                    walk(dependency)
                    seen.add(dependency)
                    output.append(dependency)
        walk(capability_id)
        return tuple(output)

    def route(self, intent: str, *, top: int = 8) -> tuple[CrossRepoMatch, ...]:
        query = _tokens(intent)
        matches: list[CrossRepoMatch] = []
        for capability in self.capabilities.values():
            repo = self.repositories[capability.repository]
            haystack = _tokens(" ".join((capability.capability_id, capability.name, *capability.domains, *capability.limitations)))
            overlap = len(query & haystack) / max(1, len(query))
            score = overlap + 0.15 * capability.evidence_weight
            if score <= 0:
                continue
            matches.append(CrossRepoMatch(
                capability_id=capability.capability_id,
                repository_identity=repo.identity,
                score=score,
                evidence_weight=capability.evidence_weight,
                maturity=capability.maturity,
                read_only=capability.read_only,
                content_disclosure="opaque_private_capability_metadata_only" if repo.visibility != "public" else "public_metadata",
                status="REUSE_CANDIDATE" if overlap >= 0.5 and capability.evidence_weight >= 0.5 else "INSPECT_OR_EXTEND",
            ))
        matches.sort(key=lambda item: (-item.score, -item.evidence_weight, item.capability_id))
        return tuple(matches[:max(0, top)])

    def build_plan(self, intent: str, *, top: int = 8) -> dict[str, Any]:
        matches = self.route(intent, top=top)
        selected_ids = [match.capability_id for match in matches]
        closure: list[str] = []
        for capability_id in selected_ids:
            for dependency in self.dependency_closure(capability_id):
                if dependency not in closure and dependency not in selected_ids:
                    closure.append(dependency)
        repository_identities: list[str] = []
        for capability_id in closure + selected_ids:
            identity = self.repositories[self.capabilities[capability_id].repository].identity
            if identity not in repository_identities:
                repository_identities.append(identity)
        payload = {
            "schema": "omega-workmax-cross-repo/v1",
            "intent": intent,
            "repository_snapshots": [self.repositories[key].to_dict() for key in sorted(self.repositories)],
            "matches": [match.to_dict() for match in matches],
            "selected_capability": selected_ids[0] if selected_ids else None,
            "selected_capabilities": selected_ids,
            "dependency_closure": closure,
            "planned_repository_identities": repository_identities,
            "cross_repository_writes_authorized": False,
            "automatic_merge_authorized": False,
            "privacy_rule": "private repository content is never embedded in routing output",
            "oak_limits": [
                "Repository snapshots are valid only for the exact bound head SHA.",
                "Lexical routing is a discovery signal, not semantic proof.",
                "Private capability metadata may route work without disclosing private content.",
                "A technical DRAFT_WRITE authority does not authorize a mutation in this plan.",
                "Cross-repository dependency closure does not imply legal, IP, safety, or deployment authority.",
            ],
        }
        canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
        payload["plan_digest"] = hashlib.sha256(canonical.encode("utf-8")).hexdigest()
        return payload

def compile_cross_repo_plan(payload: dict[str, Any]) -> dict[str, Any]:
    repositories = [RepoSnapshot(**item) for item in payload.get("repositories", [])]
    capabilities = [CrossRepoCapability.from_dict(item) for item in payload.get("capabilities", [])]
    return CrossRepoRegistry(repositories, capabilities).build_plan(
        str(payload.get("intent") or ""), top=int(payload.get("top", 8))
    )

def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="omega-workmax-cross-repo")
    parser.add_argument("input")
    parser.add_argument("--output")
    args = parser.parse_args(argv)
    payload = json.loads(Path(args.input).read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise TypeError("input must be a JSON object")
    text = json.dumps(compile_cross_repo_plan(payload), indent=2, sort_keys=True, ensure_ascii=False) + "\n"
    if args.output:
        Path(args.output).write_text(text, encoding="utf-8")
    else:
        print(text, end="")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
