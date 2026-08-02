"""Deterministic OAKGate rules for evidence, execution, privacy, and claims."""

from __future__ import annotations

import re

from .model import Claim, EpistemicLayer, EpistemicStatus, Finding, GateDecision, GateReport


_ABSOLUTE_PATTERNS: tuple[tuple[str, str], ...] = (
    (r"\bpreuve absolue\b", "Replace with the strongest evidence-bounded status."),
    (r"\b100\s*%\s+(?:de\s+)?(?:consensus|approbation|gratitude)\b", "Report observed sample size and method."),
    (r"\b(?:contr[oô]le|commande|reprogramme)\s+(?:l['’])?(?:univers|omnivers|humanit[eé]|ga[iï]a)\b", "Downgrade to MythOS or define a measurable subsystem."),
    (r"\b(?:publication|gravure|incrustation)\s+irr[eé]versible\b", "Use versioned, reviewable, reversible publication states."),
    (r"\bremplace\s+(?:la\s+)?constante\b", "Remove the physical-law claim or provide a formal derivation and evidence."),
    (r"\bextraterrestres?\s+(?:confirm[eé]s?|int[eé]gr[eé]s?|soumis)\b", "Mark as speculative unless independently verified evidence exists."),
    (r"\b(?:aucune|z[eé]ro)\s+entropie\b", "Define the system boundary and report a thermodynamic balance."),
)

_EXECUTION_WORDS = re.compile(
    r"\b(?:publi[eé]|d[eé]ploy[eé]|commit(?:t[eé])?|push(?:[eé])?|sync(?:hronis[eé])?|envoy[eé])\b",
    re.IGNORECASE,
)

_SENSITIVE_PATTERNS: tuple[tuple[str, str], ...] = (
    (r"\bn[eé]\s+[àa]\s+[A-ZÀ-ÖØ-Ý][\wÀ-ÿ'’-]+", "Remove birthplace from public technical claims."),
    (r"\b(?:le\s+)?\d{1,2}\s+(?:janvier|f[eé]vrier|mars|avril|mai|juin|juillet|ao[uû]t|septembre|octobre|novembre|d[eé]cembre)\s+\d{4}\b", "Remove full birth date from public artifacts."),
    (r"\bfils\s+de\b|\bfille\s+de\b", "Do not publish family relationships without explicit consent and necessity."),
)

_ALLOWED_IP_CLASSES = {
    "OPEN_SOURCE",
    "PUBLICATION",
    "PATENT_CANDIDATE",
    "TRADE_SECRET",
    "TRADEMARK",
    "CONFIDENTIAL",
    "NOT_APPLICABLE",
}


def _finding(
    code: str,
    severity: GateDecision,
    message: str,
    remediation: str,
) -> Finding:
    return Finding(code, severity, message, remediation)


def evaluate_claim(claim: Claim) -> GateReport:
    """Evaluate one claim with deterministic, dependency-free OAK rules."""

    findings: list[Finding] = []
    normalized = claim.text.casefold()

    if claim.status.rank >= EpistemicStatus.FORMALIZATION.rank and not claim.evidence:
        findings.append(
            _finding(
                "OAK-EVIDENCE-001",
                GateDecision.BLOCK,
                f"Status {claim.status.value} requires at least one evidence reference.",
                "Add a proof, dataset, test result, protocol, or downgrade the status.",
            )
        )

    if claim.status.rank >= EpistemicStatus.PROTOTYPE.rank and not claim.artifacts:
        findings.append(
            _finding(
                "OAK-ARTIFACT-001",
                GateDecision.BLOCK,
                f"Status {claim.status.value} requires an inspectable artifact.",
                "Link executable code, a device record, a release, or downgrade the status.",
            )
        )

    if claim.status in {
        EpistemicStatus.EMPIRICAL,
        EpistemicStatus.REPRODUCED,
        EpistemicStatus.CERTIFIED,
        EpistemicStatus.DEPLOYED,
    } and claim.uncertainty == 0.0:
        findings.append(
            _finding(
                "OAK-UNCERTAINTY-001",
                GateDecision.WARN,
                "An empirical or deployed claim reports zero uncertainty.",
                "Document measurement, model, sampling, and residual uncertainty.",
            )
        )

    if claim.ip_classification not in _ALLOWED_IP_CLASSES:
        findings.append(
            _finding(
                "OAK-IP-001",
                GateDecision.BLOCK,
                "IP classification is missing or unsupported.",
                "Classify as OPEN_SOURCE, PUBLICATION, PATENT_CANDIDATE, TRADE_SECRET, TRADEMARK, CONFIDENTIAL, or NOT_APPLICABLE.",
            )
        )

    for pattern, remediation in _ABSOLUTE_PATTERNS:
        if re.search(pattern, normalized, flags=re.IGNORECASE):
            findings.append(
                _finding(
                    "OAK-OVERCLAIM-001",
                    GateDecision.BLOCK,
                    "Absolute or reality-level claim detected without an operational boundary.",
                    remediation,
                )
            )
            break

    if _EXECUTION_WORDS.search(claim.text) and not claim.artifacts:
        findings.append(
            _finding(
                "OAK-EXECUTION-001",
                GateDecision.BLOCK,
                "An external action is described as completed without an execution artifact.",
                "Attach a commit SHA, deployment URL, signed log, message ID, or mark the action as planned.",
            )
        )

    if claim.public_intent:
        for pattern, remediation in _SENSITIVE_PATTERNS:
            if re.search(pattern, claim.text, flags=re.IGNORECASE):
                findings.append(
                    _finding(
                        "OAK-PRIVACY-001",
                        GateDecision.BLOCK,
                        "Sensitive identity or family information detected in public-intent text.",
                        remediation,
                    )
                )
                break

    if claim.source_attributions and not claim.evidence:
        findings.append(
            _finding(
                "OAK-ATTRIBUTION-001",
                GateDecision.BLOCK,
                "Opinions or actions are attributed to external people without evidence.",
                "Attach the message, publication, decision, or remove the attribution.",
            )
        )

    if claim.layer is EpistemicLayer.MYTHOS and claim.status is not EpistemicStatus.MYTH:
        findings.append(
            _finding(
                "OAK-LAYER-001",
                GateDecision.WARN,
                "MythOS content carries a non-myth epistemic status.",
                "Move it to TheoryOS with definitions or downgrade it to M0.",
            )
        )

    if not findings:
        decision = GateDecision.PASS
    elif any(item.severity is GateDecision.BLOCK for item in findings):
        decision = GateDecision.BLOCK
    else:
        decision = GateDecision.WARN

    return GateReport(claim.claim_id, decision, tuple(findings))
