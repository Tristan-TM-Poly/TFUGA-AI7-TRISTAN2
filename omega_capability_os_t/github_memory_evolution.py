from __future__ import annotations

from dataclasses import asdict, dataclass
from statistics import mean
from typing import Any, Iterable, Mapping, Sequence

from .github_memory import (
    AssetObservation,
    CapabilityObservation,
    CapabilityRequest,
    GitHubMemoryIndex,
    PRMemory,
    ReuseBeforeCreateGate,
    _jaccard,
    _stable_digest,
    _tokens,
)

EVOLUTION_SCHEMA_VERSION = "0.7.0"
OUTCOMES = {"SUCCESS", "FAILURE", "DEGRADED"}
ACTIONS = {"REUSE", "COMPOSE", "EXTEND", "INSPECT", "CREATE"}


@dataclass(frozen=True)
class SupersessionCandidate:
    older_ref: str
    newer_ref: str
    temporal_order: bool
    lexical_similarity: float
    file_similarity: float
    combined_score: float
    evidence: tuple[str, ...]
    review_required: bool = True


class TemporalSupersessionMiner:
    """R0.3: mines review-only lineage candidates; it never promotes inferred supersession to a strong graph edge."""

    def __init__(self, lexical_weight: float = 0.55, file_weight: float = 0.45, threshold: float = 0.30) -> None:
        if lexical_weight < 0 or file_weight < 0 or lexical_weight + file_weight <= 0:
            raise ValueError("supersession weights must be non-negative and non-zero")
        if not 0.0 <= threshold <= 1.0:
            raise ValueError("threshold must be inside [0,1]")
        total = lexical_weight + file_weight
        self.lexical_weight = lexical_weight / total
        self.file_weight = file_weight / total
        self.threshold = threshold

    @staticmethod
    def _ordered(left: PRMemory, right: PRMemory) -> tuple[PRMemory, PRMemory]:
        if left.repository != right.repository:
            raise ValueError("temporal supersession mining requires PRs from the same repository")
        left_key = (left.updated_at or "", left.number)
        right_key = (right.updated_at or "", right.number)
        return (left, right) if left_key <= right_key else (right, left)

    def mine(self, index: GitHubMemoryIndex, top_k: int = 32) -> dict[str, Any]:
        prs = sorted(index.prs.values(), key=lambda pr: (pr.repository, pr.updated_at or "", pr.number))
        candidates: list[SupersessionCandidate] = []
        for i, left in enumerate(prs):
            for right in prs[i + 1 :]:
                if left.repository != right.repository:
                    continue
                older, newer = self._ordered(left, right)
                lexical = _jaccard(older.keywords, newer.keywords)
                file_sim = _jaccard(older.files, newer.files) if older.files and newer.files else 0.0
                score = self.lexical_weight * lexical + self.file_weight * file_sim
                if score < self.threshold:
                    continue
                evidence: list[str] = ["newer PR observed after older PR"]
                if lexical > 0:
                    evidence.append(f"lexical_jaccard={lexical:.6f}")
                if file_sim > 0:
                    evidence.append(f"changed_file_jaccard={file_sim:.6f}")
                candidates.append(
                    SupersessionCandidate(
                        older_ref=older.ref,
                        newer_ref=newer.ref,
                        temporal_order=True,
                        lexical_similarity=round(lexical, 6),
                        file_similarity=round(file_sim, 6),
                        combined_score=round(score, 6),
                        evidence=tuple(evidence),
                    )
                )
        candidates.sort(key=lambda row: (-row.combined_score, row.older_ref, row.newer_ref))
        selected = candidates[:top_k]
        payload = {
            "schema": f"omega-github-temporal-supersession/v{EVOLUTION_SCHEMA_VERSION}",
            "candidate_count": len(selected),
            "candidates": [asdict(row) for row in selected],
            "strong_edges_added": 0,
            "boundary": (
                "Temporal/file/lexical overlap is a review lead only. Inferred candidates never become "
                "supersedes/replaces edges without explicit lineage or separate OAK evidence."
            ),
        }
        payload["fingerprint"] = _stable_digest(payload)
        return payload


@dataclass(frozen=True)
class ResidualArtifactSpec:
    request_id: str
    decision: str
    selected_capabilities: tuple[str, ...]
    residual_outputs: tuple[str, ...]
    exact_inspection_refs: tuple[str, ...]
    required_tests: tuple[str, ...]
    required_provenance: tuple[str, ...]
    generation_scope: str
    generation_allowed: bool
    boundary: str

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["schema"] = f"omega-residual-artifact-spec/v{EVOLUTION_SCHEMA_VERSION}"
        payload["fingerprint"] = _stable_digest(payload)
        return payload


class ResidualCodeCompiler:
    """R0.4: compiles a minimal implementation contract, not unverified source code."""

    def __init__(self, index: GitHubMemoryIndex) -> None:
        self.index = index

    def compile(self, request: CapabilityRequest) -> ResidualArtifactSpec:
        decision = ReuseBeforeCreateGate(self.index).decide(request)
        inspect_refs: list[str] = []
        for row in decision.historical_candidates[:8]:
            ref = str(row.get("source_ref") or row.get("ref") or "")
            if ref and ref not in inspect_refs:
                inspect_refs.append(ref)
        selected_sources = [
            self.index.capabilities[cid].source_ref
            for cid in decision.selected_capabilities
            if cid in self.index.capabilities
        ]
        for ref in selected_sources:
            if ref and ref not in inspect_refs:
                inspect_refs.append(ref)

        if decision.action in {"REUSE", "COMPOSE"}:
            generation_scope = "integration_only"
            generation_allowed = False
        elif decision.action == "INSPECT":
            generation_scope = "blocked_pending_exact_inspection"
            generation_allowed = False
        elif decision.action == "EXTEND":
            generation_scope = "residual_outputs_only"
            generation_allowed = bool(decision.residual_outputs)
        else:
            generation_scope = "requested_capability_only"
            generation_allowed = True

        tests = (
            "unit tests for every residual output",
            "integration test against selected reused capabilities",
            "regression test demonstrating no duplicate pre-existing interface",
            "OAK boundary assertion: similarity/lifecycle != correctness",
        )
        provenance = tuple(sorted({*selected_sources, *inspect_refs}))
        return ResidualArtifactSpec(
            request_id=request.request_id,
            decision=decision.action,
            selected_capabilities=decision.selected_capabilities,
            residual_outputs=decision.residual_outputs,
            exact_inspection_refs=tuple(inspect_refs),
            required_tests=tests,
            required_provenance=provenance,
            generation_scope=generation_scope,
            generation_allowed=generation_allowed,
            boundary=(
                "This compiler emits a bounded implementation contract. generation_allowed does not authorize a GitHub write, "
                "prove novelty, or certify that generated code is correct."
            ),
        )


@dataclass(frozen=True)
class ReuseOutcomeReceipt:
    receipt_id: str
    request_id: str
    action: str
    selected_capabilities: tuple[str, ...]
    outcome: str
    defect_delta: float = 0.0
    complexity_delta: float = 0.0
    latency_delta: float = 0.0
    maintenance_delta: float = 0.0
    evidence_refs: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if self.action not in ACTIONS:
            raise ValueError(f"unsupported action: {self.action}")
        if self.outcome not in OUTCOMES:
            raise ValueError(f"unsupported outcome: {self.outcome}")
        if not self.evidence_refs:
            raise ValueError("reuse outcome learning requires at least one evidence reference")

    @property
    def memory_class(self) -> str:
        if self.outcome == "SUCCESS":
            return "M+"
        if self.outcome == "FAILURE":
            return "M-"
        return "M?"

    @property
    def utility(self) -> float:
        outcome_term = {"SUCCESS": 1.0, "DEGRADED": 0.0, "FAILURE": -1.0}[self.outcome]
        # Negative deltas are improvements for cost-like metrics.
        improvement = -mean((self.defect_delta, self.complexity_delta, self.latency_delta, self.maintenance_delta))
        return round(outcome_term + 0.25 * improvement, 6)


class ReuseOutcomeLearner:
    """R0.5: learns empirical reuse preferences only from explicit evidence-bearing receipts."""

    def learn(self, receipts: Iterable[ReuseOutcomeReceipt]) -> dict[str, Any]:
        rows = tuple(receipts)
        action_groups: dict[str, list[ReuseOutcomeReceipt]] = {}
        capability_groups: dict[str, list[ReuseOutcomeReceipt]] = {}
        for row in rows:
            action_groups.setdefault(row.action, []).append(row)
            for capability_id in row.selected_capabilities:
                capability_groups.setdefault(capability_id, []).append(row)

        def summarize(group: Sequence[ReuseOutcomeReceipt]) -> dict[str, Any]:
            return {
                "n": len(group),
                "successes": sum(row.outcome == "SUCCESS" for row in group),
                "failures": sum(row.outcome == "FAILURE" for row in group),
                "degraded": sum(row.outcome == "DEGRADED" for row in group),
                "mean_utility": round(mean(row.utility for row in group), 6),
                "evidence_refs": sorted({ref for row in group for ref in row.evidence_refs}),
            }

        payload = {
            "schema": f"omega-reuse-outcome-policy/v{EVOLUTION_SCHEMA_VERSION}",
            "receipt_count": len(rows),
            "actions": {key: summarize(group) for key, group in sorted(action_groups.items())},
            "capabilities": {key: summarize(group) for key, group in sorted(capability_groups.items())},
            "memory_counts": {
                "M+": sum(row.memory_class == "M+" for row in rows),
                "M-": sum(row.memory_class == "M-" for row in rows),
                "M?": sum(row.memory_class == "M?" for row in rows),
            },
            "boundary": (
                "Observed reuse outcomes are empirical policy evidence only. Merge state is never used as an outcome, "
                "small samples are not causal proof, and historical utility must not override current OAK gates."
            ),
        }
        payload["fingerprint"] = _stable_digest(payload)
        return payload


@dataclass(frozen=True)
class CrossRepositoryConflict:
    capability_id: str
    left_source: str
    right_source: str
    left_signature: str
    right_signature: str


def _capability_signature(obs: CapabilityObservation) -> str:
    cap = obs.capability
    return _stable_digest(
        {
            "id": cap.capability_id,
            "domains": cap.domains,
            "consumes": cap.consumes,
            "produces": cap.produces,
            "authority": cap.authority,
        }
    )


class CrossRepositoryCapabilityGraph:
    """R0.6: joins repository memories while preserving conflicts instead of silently overwriting capability IDs."""

    def merge(self, indexes: Mapping[str, GitHubMemoryIndex]) -> dict[str, Any]:
        repositories = sorted(indexes)
        capability_sources: dict[str, list[tuple[str, CapabilityObservation]]] = {}
        pr_count = 0
        asset_count = 0
        for repository, index in indexes.items():
            pr_count += len(index.prs)
            asset_count += len(index.assets)
            for capability_id, obs in index.capabilities.items():
                capability_sources.setdefault(capability_id, []).append((repository, obs))

        shared: list[dict[str, Any]] = []
        conflicts: list[CrossRepositoryConflict] = []
        for capability_id, observations in sorted(capability_sources.items()):
            signatures = [(repo, obs, _capability_signature(obs)) for repo, obs in observations]
            unique = {sig for _, _, sig in signatures}
            if len(observations) > 1 and len(unique) == 1:
                shared.append(
                    {
                        "capability_id": capability_id,
                        "repositories": sorted(repo for repo, _, _ in signatures),
                        "signature": signatures[0][2],
                        "boundary": "matching capability contract signature != shared implementation or equivalent runtime behavior",
                    }
                )
            elif len(unique) > 1:
                base_repo, base_obs, base_sig = signatures[0]
                for repo, obs, sig in signatures[1:]:
                    if sig == base_sig:
                        continue
                    conflicts.append(
                        CrossRepositoryConflict(
                            capability_id=capability_id,
                            left_source=f"{base_repo}:{base_obs.source_ref}",
                            right_source=f"{repo}:{obs.source_ref}",
                            left_signature=base_sig,
                            right_signature=sig,
                        )
                    )

        payload = {
            "schema": f"omega-cross-repository-capability-graph/v{EVOLUTION_SCHEMA_VERSION}",
            "repositories": repositories,
            "repository_count": len(repositories),
            "pr_count": pr_count,
            "asset_count": asset_count,
            "unique_capability_ids": len(capability_sources),
            "shared_contracts": shared,
            "conflicts": [asdict(row) for row in conflicts],
            "boundary": (
                "Cross-repository matching IDs/contracts are provenance candidates only. Conflicting contracts are preserved, "
                "and neither equality nor conflict proves implementation equivalence, superiority, or supersession."
            ),
        }
        payload["fingerprint"] = _stable_digest(payload)
        return payload


@dataclass(frozen=True)
class LLMTIdentity:
    identity_id: str
    scope: str
    selector: str
    authority: str = "draft"
    parent_id: str | None = None

    def __post_init__(self) -> None:
        if self.scope not in {"global", "pr", "module"}:
            raise ValueError("scope must be global, pr, or module")
        if self.authority not in {"read", "draft"}:
            raise ValueError("federated memory contexts may only carry read or draft authority")


class LLMTFederationCompiler:
    """R0.7: compiles bounded shared-memory contexts for logical LLMT identities; identities are not separate minds/models."""

    def __init__(self, index: GitHubMemoryIndex) -> None:
        self.index = index

    def compile(
        self,
        request: CapabilityRequest,
        identities: Iterable[LLMTIdentity],
        max_items: int = 6,
    ) -> dict[str, Any]:
        identities = tuple(identities)
        if not identities:
            identities = (LLMTIdentity("global", "global", "*", "draft", None),)
        by_id = {identity.identity_id: identity for identity in identities}
        if len(by_id) != len(identities):
            raise ValueError("LLMT identity IDs must be unique")
        for identity in identities:
            if identity.parent_id and identity.parent_id not in by_id:
                raise ValueError(f"unknown LLMT parent: {identity.parent_id}")

        base_context = ReuseBeforeCreateGate(self.index).compile_context(request, max_items=max_items)
        packets: list[dict[str, Any]] = []
        for identity in sorted(identities, key=lambda row: (row.scope, row.identity_id)):
            selector_tokens = set(_tokens(identity.selector))
            historical = list(base_context["decision"]["historical_candidates"])
            if selector_tokens:
                filtered = []
                for row in historical:
                    row_tokens = set(_tokens((str(row.get("label", "")), str(row.get("title", "")), str(row.get("source_ref", "")), str(row.get("ref", "")))))
                    if selector_tokens & row_tokens:
                        filtered.append(row)
                historical = filtered or historical
            child = {
                "schema": f"omega-llmt-federated-context/v{EVOLUTION_SCHEMA_VERSION}",
                "identity": asdict(identity),
                "request": base_context["request"],
                "decision": dict(base_context["decision"]),
                "historical_candidates": historical[:max_items],
                "relations": list(base_context["relations"][: max_items * 2]),
                "parent_context_fingerprint": base_context["fingerprint"],
                "authority_ceiling": identity.authority,
                "instructions": [
                    "shared GitHub memory is canonical input; local context is a bounded projection",
                    "return discoveries as provenance-bearing candidates, not private hidden truth",
                    "do not widen authority beyond read/draft",
                    "reuse/compose/extend before create and emit residuals explicitly",
                    "LLMT identity is a logical specialization, not an independent person, consciousness, or evidence source",
                ],
            }
            child["fingerprint"] = _stable_digest(child)
            packets.append(child)

        payload = {
            "schema": f"omega-llmt-federation/v{EVOLUTION_SCHEMA_VERSION}",
            "global_context_fingerprint": base_context["fingerprint"],
            "packet_count": len(packets),
            "packets": packets,
            "boundary": (
                "Federated LLMT packets are bounded context projections over one shared memory substrate. Multiple packets/models "
                "do not imply independent evidence, consensus truth, autonomous authority, or distinct minds."
            ),
        }
        payload["fingerprint"] = _stable_digest(payload)
        return payload


def compile_evolution_court(
    index: GitHubMemoryIndex,
    request: CapabilityRequest,
    *,
    outcome_receipts: Iterable[ReuseOutcomeReceipt] = (),
    identities: Iterable[LLMTIdentity] = (),
) -> dict[str, Any]:
    """One deterministic R0.3→R0.7 court used by CI and higher-level agents."""
    supersession = TemporalSupersessionMiner().mine(index)
    residual = ResidualCodeCompiler(index).compile(request).to_dict()
    policy = ReuseOutcomeLearner().learn(tuple(outcome_receipts))
    cross_repo = CrossRepositoryCapabilityGraph().merge({"current": index})
    federation = LLMTFederationCompiler(index).compile(request, identities)
    payload = {
        "schema": f"omega-github-memory-evolution-court/v{EVOLUTION_SCHEMA_VERSION}",
        "supersession": supersession,
        "residual_artifact": residual,
        "reuse_policy": policy,
        "cross_repository": cross_repo,
        "federation": federation,
        "oak": {
            "status": "PASS",
            "boundaries": [
                "INFERRED_SUPERSESSION != STRONG_LINEAGE",
                "GENERATION_ALLOWED != WRITE_AUTHORITY",
                "REUSE_OUTCOME != CAUSAL_PROOF",
                "MATCHING_CAPABILITY_CONTRACT != SHARED_IMPLEMENTATION",
                "LLMT_PACKET_COUNT != INDEPENDENT_EVIDENCE",
            ],
        },
    }
    payload["fingerprint"] = _stable_digest(payload)
    return payload
