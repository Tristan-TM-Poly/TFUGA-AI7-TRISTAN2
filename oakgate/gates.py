"""Deterministic OAKGate rules for evidence, execution, privacy, IP, and U²."""

from __future__ import annotations

import re

from .config import DEFAULT_RULE_PACK, RulePack
from .model import (
    Claim,
    EpistemicLayer,
    EpistemicStatus,
    Finding,
    GateDecision,
    GateReport,
    SourceLocation,
)
from .provenance import verify_claim_provenance
from .uncertainty import assess_confidence


_EXECUTION_WORDS = re.compile(
    r"\b(?:publi[eé]|d[eé]ploy[eé]|commit(?:t[eé])?|push(?:[eé])?|"
    r"sync(?:hronis[eé])?|envoy[eé]|fusionn[eé]|mis[e]?\s+en\s+production)\b",
    re.IGNORECASE,
)

_SENSITIVE_PATTERNS: tuple[tuple[str, str], ...] = (
    (
        r"\bn[eé]\s+[àa]\s+[A-ZÀ-ÖØ-Ý][\wÀ-ÿ'’-]+",
        "Remove birthplace from public technical claims.",
    ),
    (
        r"\b(?:le\s+)?\d{1,2}\s+"
        r"(?:janvier|f[eé]vrier|mars|avril|mai|juin|juillet|ao[uû]t|"
        r"septembre|octobre|novembre|d[eé]cembre)\s+\d{4}\b",
        "Remove full birth date from public artifacts.",
    ),
    (
        r"\bfils\s+de\b|\bfille\s+de\b",
        "Do not publish family relationships without explicit consent and necessity.",
    ),
    (
        r"\b\d{3}[-.\s]\d{3}[-.\s]\d{4}\b",
        "Remove personal phone numbers from public technical claims.",
    ),
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

_NON_PUBLIC_IP_CLASSES = {"PATENT_CANDIDATE", "TRADE_SECRET", "CONFIDENTIAL"}


def _finding(
    code: str,
    severity: GateDecision,
    message: str,
    remediation: str,
) -> Finding:
    return Finding(code, severity, message, remediation)


def evaluate_claim(
    claim: Claim,
    *,
    rule_pack: RulePack | None = None,
    source: SourceLocation | None = None,
) -> GateReport:
    """Evaluate one claim with deterministic, dependency-free OAK rules."""

    findings: list[Finding] = []
    pack = rule_pack or DEFAULT_RULE_PACK

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

    if claim.ip_classification not in _ALLOWED_IP_CLASSES:
        findings.append(
            _finding(
                "OAK-IP-001",
                GateDecision.BLOCK,
                "IP classification is missing or unsupported.",
                "Classify as OPEN_SOURCE, PUBLICATION, PATENT_CANDIDATE, "
                "TRADE_SECRET, TRADEMARK, CONFIDENTIAL, or NOT_APPLICABLE.",
            )
        )

    if claim.public_intent and claim.ip_classification in _NON_PUBLIC_IP_CLASSES:
        findings.append(
            _finding(
                "OAK-IP-PUBLIC-001",
                GateDecision.BLOCK,
                "Public intent conflicts with a non-public IP classification.",
                "Run IPGate and remove public intent until disclosure is authorized.",
            )
        )

    for rule in pack.rules:
        if rule.compile().search(claim.text):
            findings.append(
                _finding(rule.code, rule.severity, rule.message, rule.remediation)
            )

    if _EXECUTION_WORDS.search(claim.text) and not claim.artifacts:
        findings.append(
            _finding(
                "OAK-EXECUTION-001",
                GateDecision.BLOCK,
                "An external action is described as completed without an execution artifact.",
                "Attach a commit SHA, deployment URL, signed log, message ID, "
                "or mark the action as planned.",
            )
        )

    if "irreversible_publication" in {risk.casefold() for risk in claim.risks}:
        findings.append(
            _finding(
                "OAK-RISK-IRREVERSIBLE-001",
                GateDecision.BLOCK,
                "The risk register explicitly contains irreversible publication.",
                "Replace it with a versioned, retractable, human-approved release process.",
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

    if (
        claim.layer is EpistemicLayer.REALITY
        and claim.status.rank < EpistemicStatus.EMPIRICAL.rank
    ):
        findings.append(
            _finding(
                "OAK-LAYER-REALITY-001",
                GateDecision.WARN,
                "RealityOS content is below the empirical evidence level.",
                "Move it to TheoryOS/PrototypeOS or collect an observed measurement.",
            )
        )

    if claim.provenance_hash is not None and not verify_claim_provenance(claim):
        findings.append(
            _finding(
                "OAK-PROVENANCE-001",
                GateDecision.BLOCK,
                "The supplied provenance hash does not match the canonical claim payload.",
                "Recompute the SHA-256 hash after the final reviewed change.",
            )
        )

    confidence = assess_confidence(claim)
    if confidence.debt >= 0.50:
        findings.append(
            _finding(
                "OAK-U2-DEBT-001",
                GateDecision.BLOCK,
                f"Severe confidence debt detected ({confidence.debt:.2f}).",
                "Increase uncertainty, downgrade status, or add evidence and artifacts.",
            )
        )
    elif confidence.debt >= 0.25:
        findings.append(
            _finding(
                "OAK-U2-DEBT-001",
                GateDecision.WARN,
                f"Confidence debt detected ({confidence.debt:.2f}).",
                "Increase uncertainty or strengthen the evidence package.",
            )
        )

    if not findings:
        decision = GateDecision.PASS
    elif any(item.severity is GateDecision.BLOCK for item in findings):
        decision = GateDecision.BLOCK
    else:
        decision = GateDecision.WARN

    return GateReport(
        claim_id=claim.claim_id,
        decision=decision,
        findings=tuple(findings),
        source=source,
        confidence_debt=confidence.debt,
        justified_confidence=confidence.justified,
    )
