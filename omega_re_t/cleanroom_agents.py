"""Role-separated clean-room reconstruction records and audits."""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from hashlib import sha256
from json import dumps
from typing import Mapping, Sequence


class CleanRoomRole(str, Enum):
    OBSERVER = "observer"
    SPECIFIER = "specifier"
    IMPLEMENTER = "implementer"
    AUDITOR = "auditor"


@dataclass(frozen=True, slots=True)
class AgentIdentity:
    agent_id: str
    role: CleanRoomRole
    allowed_inputs: tuple[str, ...]
    forbidden_inputs: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class CleanRoomArtifact:
    artifact_id: str
    artifact_type: str
    author_agent_id: str
    source_artifact_ids: tuple[str, ...]
    content_digest: str
    claims: Mapping[str, str] = field(default_factory=dict)
    contains_restricted_material: bool = False

    @classmethod
    def from_text(
        cls,
        artifact_id: str,
        artifact_type: str,
        author_agent_id: str,
        text: str,
        *,
        source_artifact_ids: Sequence[str] = (),
        claims: Mapping[str, str] | None = None,
        contains_restricted_material: bool = False,
    ) -> "CleanRoomArtifact":
        return cls(
            artifact_id,
            artifact_type,
            author_agent_id,
            tuple(source_artifact_ids),
            sha256(text.encode("utf-8")).hexdigest(),
            dict(claims or {}),
            contains_restricted_material,
        )


@dataclass(slots=True)
class CleanRoomLedger:
    agents: dict[str, AgentIdentity] = field(default_factory=dict)
    artifacts: dict[str, CleanRoomArtifact] = field(default_factory=dict)

    def register_agent(self, agent: AgentIdentity) -> None:
        if agent.agent_id in self.agents:
            raise ValueError("duplicate agent")
        self.agents[agent.agent_id] = agent

    def add_artifact(self, artifact: CleanRoomArtifact) -> None:
        if artifact.artifact_id in self.artifacts:
            raise ValueError("duplicate artifact")
        if artifact.author_agent_id not in self.agents:
            raise ValueError("unknown author agent")
        if any(source not in self.artifacts for source in artifact.source_artifact_ids):
            raise ValueError("artifact references unknown source")
        self.artifacts[artifact.artifact_id] = artifact

    def descendants(self, artifact_id: str) -> frozenset[str]:
        result: set[str] = set()
        changed = True
        while changed:
            changed = False
            for candidate in self.artifacts.values():
                if candidate.artifact_id in result:
                    continue
                if artifact_id in candidate.source_artifact_ids or any(source in result for source in candidate.source_artifact_ids):
                    result.add(candidate.artifact_id)
                    changed = True
        return frozenset(result)

    def digest(self) -> str:
        payload = {
            "agents": {
                key: {
                    "role": value.role.value,
                    "allowed_inputs": value.allowed_inputs,
                    "forbidden_inputs": value.forbidden_inputs,
                }
                for key, value in sorted(self.agents.items())
            },
            "artifacts": {
                key: {
                    "type": value.artifact_type,
                    "author": value.author_agent_id,
                    "sources": value.source_artifact_ids,
                    "content_digest": value.content_digest,
                    "claims": dict(sorted(value.claims.items())),
                    "contains_restricted_material": value.contains_restricted_material,
                }
                for key, value in sorted(self.artifacts.items())
            },
        }
        return sha256(dumps(payload, sort_keys=True).encode()).hexdigest()


@dataclass(frozen=True, slots=True)
class CleanRoomAudit:
    passed: bool
    blockers: tuple[str, ...]
    warnings: tuple[str, ...]
    role_separation_score: float
    provenance_coverage: float
    ledger_digest: str


def audit_clean_room(ledger: CleanRoomLedger) -> CleanRoomAudit:
    blockers: list[str] = []
    warnings: list[str] = []
    if not ledger.agents:
        blockers.append("No agents are registered.")
    roles = {agent.role for agent in ledger.agents.values()}
    required = {CleanRoomRole.OBSERVER, CleanRoomRole.SPECIFIER, CleanRoomRole.IMPLEMENTER, CleanRoomRole.AUDITOR}
    missing = required - roles
    if missing:
        blockers.append("Missing roles: " + ", ".join(sorted(role.value for role in missing)))
    for artifact in ledger.artifacts.values():
        author = ledger.agents[artifact.author_agent_id]
        if artifact.contains_restricted_material and author.role is not CleanRoomRole.OBSERVER:
            blockers.append(f"Restricted material propagated to {author.role.value} artifact {artifact.artifact_id}.")
        for source_id in artifact.source_artifact_ids:
            source = ledger.artifacts[source_id]
            source_author = ledger.agents[source.author_agent_id]
            if source.contains_restricted_material and author.role in {CleanRoomRole.IMPLEMENTER, CleanRoomRole.SPECIFIER}:
                blockers.append(f"Forbidden source path {source_id} -> {artifact.artifact_id}.")
            if source_author.role is CleanRoomRole.IMPLEMENTER and author.role is CleanRoomRole.SPECIFIER:
                warnings.append("Specification depends on an implementation artifact, weakening independence.")
    authored_roles = {ledger.agents[item.author_agent_id].role for item in ledger.artifacts.values()}
    separation = len(authored_roles & required) / len(required)
    with_sources = sum(bool(item.source_artifact_ids) or item.artifact_type == "observation" for item in ledger.artifacts.values())
    coverage = with_sources / max(1, len(ledger.artifacts))
    return CleanRoomAudit(not blockers, tuple(sorted(set(blockers))), tuple(sorted(set(warnings))), separation, coverage, ledger.digest())
