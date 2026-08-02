"""Canonical 8×8 diversification registry.

The registry is a routing catalogue, not evidence that every module has been
implemented or scientifically validated.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any, Iterable


@dataclass(frozen=True)
class DiversificationModule:
    group: str
    name: str
    role: str
    required_evidence: str
    first_gate: str
    risk: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


_GROUPS: dict[str, tuple[tuple[str, str, str, str, str], ...]] = {
    "knowledge": (
        ("KnowledgeCell Compiler", "Compile structured knowledge into auditable cells.", "schema round-trip", "cell validation", "false certainty"),
        ("Claim Atomizer", "Split broad prose into scoped claims.", "claim/source trace", "scope audit", "semantic fragmentation"),
        ("Definition Resolver", "Track competing definitions and validity domains.", "definition provenance", "ambiguity report", "premature unification"),
        ("Equation Linker", "Connect equations to claims, units and code.", "equation/source mapping", "dimension audit", "symbol mismatch"),
        ("Unit Graph", "Propagate units and calibration references.", "unit metadata", "dimensional consistency", "unit laundering"),
        ("Evidence Ledger", "Record supporting and contradicting evidence.", "typed evidence", "reference integrity", "circular support"),
        ("Contradiction Engine", "Detect candidate contradictions and scope tensions.", "paired claims", "human review queue", "false contradiction"),
        ("Temporal Canon", "Version claims and OAK transitions over time.", "transition history", "staleness audit", "obsolete canon"),
    ),
    "experiments": (
        ("Experiment Generator", "Generate bounded, reversible experiment candidates.", "protocol specification", "safety and feasibility", "unsafe automation"),
        ("Information Gain Ranker", "Rank tests by expected discrimination.", "predictive distributions", "baseline comparison", "score theatre"),
        ("Baseline Enforcer", "Require credible standard comparators.", "baseline implementation", "fairness audit", "strawman baseline"),
        ("Control Group Designer", "Attach controls and negative controls.", "control rationale", "protocol audit", "confounding"),
        ("Replication Planner", "Plan independent and repeated tests.", "replication protocol", "independence audit", "pseudo-replication"),
        ("Uncertainty Compiler", "Represent measurement and model uncertainty.", "calibration record", "propagation audit", "confidence laundering"),
        ("Residual Analyzer", "Inspect structured model failures.", "residual traces", "whiteness/structure tests", "overfitting"),
        ("Counterexample Generator", "Search bounded falsifying cases.", "generated counterexamples", "reproduction test", "invalid domain"),
    ),
    "generators": (
        ("Continuous Generator Finder", "Infer local continuous transformation generators.", "trajectory fit", "holdout reconstruction", "local/global confusion"),
        ("Discrete Event Finder", "Detect jumps and regime changes.", "event labels", "change-point benchmark", "noise overinterpretation"),
        ("Symmetry Detector", "Find candidate invariances.", "transformation tests", "group closure checks", "spurious symmetry"),
        ("Commutator Analyzer", "Measure non-commuting transformation order.", "ordered experiments", "commutator baseline", "numerical artefact"),
        ("Holonomy Detector", "Measure loop-dependent residual transforms.", "closed-loop data", "path audit", "drift confusion"),
        ("Koopman/SINDy Bridge", "Compare interpretable operator baselines.", "baseline models", "out-of-sample test", "library bias"),
        ("Causal Mechanism Ranker", "Rank mechanism classes without declaring causality.", "intervention predictions", "discriminating test", "causal overclaim"),
        ("Generator Syndrome Engine", "Compare expected and observed operators.", "operator residuals", "fault benchmark", "model misspecification"),
    ),
    "software": (
        ("Repository Twin", "Represent code, docs, tests and dependencies as a graph.", "repository snapshot", "round-trip audit", "stale mirror"),
        ("Documentation Auditor", "Detect code-documentation divergence.", "claims and symbols", "known-fixture benchmark", "false positives"),
        ("Test Generator", "Generate positive and negative tests.", "generated tests", "mutation score", "tautological tests"),
        ("CI Failure Synthesizer", "Compress failures into ranked root-cause candidates.", "CI logs", "diagnostic accuracy", "hallucinated cause"),
        ("Dependency Risk Graph", "Map licenses, versions and vulnerabilities.", "SBOM/provenance", "source verification", "stale advisory"),
        ("Performance Profiler", "Measure resource and scaling behaviour.", "benchmarks", "repeatability audit", "benchmark gaming"),
        ("Rollback Compiler", "Generate reversible change plans.", "rollback manifest", "restore test", "partial rollback"),
        ("Self-Healing Sandbox", "Test repairs before controlled deployment.", "sandbox evidence", "approval gate", "unsafe mutation"),
    ),
    "memory": (
        ("M⁻ Scientific Registry", "Store refuted hypotheses and forbidden inferences.", "failed experiment", "replay audit", "overgeneralized failure"),
        ("M⁻ Software Registry", "Store bugs, triggers and prevention tests.", "regression test", "recurrence audit", "stale workaround"),
        ("M⁻ Product Registry", "Store invalidated user and pricing assumptions.", "user evidence", "segment audit", "market overgeneralization"),
        ("M⁺ Success Registry", "Store reproducible success patterns.", "replicated result", "transfer test", "survivorship bias"),
        ("Error Recurrence Detector", "Detect previously seen failure structures.", "failure fingerprints", "precision/recall benchmark", "false match"),
        ("Failure Transfer Engine", "Test whether lessons transfer across domains.", "cross-domain trials", "scope gate", "analogy abuse"),
        ("Forbidden Inference Gate", "Block conclusions invalidated by prior evidence.", "linked rule", "override audit", "excessive blocking"),
        ("Anti-Hallucination Memory", "Record unsupported generations and their triggers.", "grounded counterexample", "repetition benchmark", "memory poisoning"),
    ),
    "value": (
        ("User Pain Graph", "Map tasks, frequency, cost and observable pain.", "user interviews", "pain verification", "invented demand"),
        ("Offer Generator", "Generate testable offers from validated pains.", "offer hypotheses", "user test", "feature inflation"),
        ("Product Evidence Cell", "Connect product claims to usage evidence.", "usage telemetry", "claim audit", "proxy metric"),
        ("Pricing Experiment Planner", "Design ethical pricing tests.", "consent and protocol", "segment analysis", "exploitative pricing"),
        ("Revenue Evidence Ledger", "Record actual rather than projected revenue evidence.", "transaction record", "accounting audit", "forecast as fact"),
        ("Maintenance Cost Predictor", "Estimate support and lifecycle costs.", "historical effort", "calibration audit", "hidden labor"),
        ("Adoption Friction Mapper", "Measure onboarding and integration barriers.", "funnel evidence", "drop-off analysis", "selection bias"),
        ("Product–Market OAKGate", "Separate market hypotheses from validated traction.", "external usage", "cohort audit", "vanity metrics"),
    ),
    "ip_security": (
        ("IP Classifier", "Route artifacts to publish, patent, secret or review.", "provenance and novelty notes", "human IP review", "legal overclaim"),
        ("Prior-Art Mapper", "Map potentially relevant public prior art.", "source records", "coverage review", "missed prior art"),
        ("License Compatibility Graph", "Check dependency license combinations.", "license texts", "legal review queue", "license misclassification"),
        ("Privacy Gate", "Detect personal and confidential data exposure.", "data inventory", "redaction test", "privacy leakage"),
        ("Permission Ledger", "Record authorization scope for actions and data.", "permission records", "expiry audit", "scope creep"),
        ("Human Approval Gate", "Require approval for sensitive irreversible actions.", "approval token", "identity audit", "rubber stamping"),
        ("Irreversibility Detector", "Classify deployment, disclosure and physical risk.", "action model", "rollback analysis", "unknown consequence"),
        ("Publication Risk Engine", "Score disclosure and claim risks.", "release candidate", "OAK/IP review", "overblocking"),
    ),
    "governance": (
        ("ScaleConductor", "Govern volume with measured finite resources.", "telemetry", "resource gate", "volume worship"),
        ("QualityConductor", "Govern evidence density and noise.", "quality metrics", "anti-inflation audit", "metric gaming"),
        ("ExperimentConductor", "Allocate tests by information gain and safety.", "portfolio scores", "ablation benchmark", "score bias"),
        ("RiskConductor", "Route safety, privacy, IP and legal risks.", "risk records", "human escalation", "risk blindness"),
        ("ProductConductor", "Allocate product experiments by external evidence.", "user evidence", "cohort comparison", "premature scaling"),
        ("PortfolioConductor", "Balance exploration and exploitation.", "branch metrics", "resource audit", "monoculture"),
        ("Canon Promotion Engine", "Promote only claims with required evidence.", "promotion packet", "independent review", "internal circularity"),
        ("Sovereignty Kernel", "Preserve human control over consequential actions.", "approval policy", "override audit", "autonomy creep"),
    ),
}


def build_registry() -> tuple[DiversificationModule, ...]:
    modules: list[DiversificationModule] = []
    for group, rows in _GROUPS.items():
        for name, role, evidence, gate, risk in rows:
            modules.append(
                DiversificationModule(
                    group=group,
                    name=name,
                    role=role,
                    required_evidence=evidence,
                    first_gate=gate,
                    risk=risk,
                )
            )
    if len(modules) != 64:
        raise AssertionError(f"expected 64 modules, got {len(modules)}")
    if len({module.name for module in modules}) != 64:
        raise AssertionError("module names must be unique")
    return tuple(modules)


REGISTRY = build_registry()


def registry_by_group() -> dict[str, tuple[DiversificationModule, ...]]:
    result: dict[str, list[DiversificationModule]] = {}
    for module in REGISTRY:
        result.setdefault(module.group, []).append(module)
    return {key: tuple(value) for key, value in result.items()}


def registry_payload() -> dict[str, Any]:
    groups = registry_by_group()
    return {
        "module_count": len(REGISTRY),
        "group_count": len(groups),
        "groups": {
            group: [module.to_dict() for module in modules]
            for group, modules in sorted(groups.items())
        },
        "boundary": (
            "The registry is an implementation and research roadmap. Presence in the "
            "catalogue is not evidence of scientific validity, product demand, or safety."
        ),
    }
