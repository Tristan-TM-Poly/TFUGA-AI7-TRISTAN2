"""Configurable regex rule packs for OAKGate."""

from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
import re
from typing import Any

from .model import GateDecision


@dataclass(frozen=True)
class PatternRule:
    code: str
    pattern: str
    severity: GateDecision
    message: str
    remediation: str

    def compile(self) -> re.Pattern[str]:
        try:
            return re.compile(self.pattern, re.IGNORECASE)
        except re.error as exc:
            raise ValueError(f"invalid regex for rule {self.code}: {exc}") from exc


@dataclass(frozen=True)
class RulePack:
    name: str
    version: str
    rules: tuple[PatternRule, ...]

    @classmethod
    def from_dict(cls, raw: dict[str, Any]) -> "RulePack":
        name = str(raw.get("name", "")).strip()
        version = str(raw.get("version", "")).strip()
        if not name or not version:
            raise ValueError("rule pack requires non-empty name and version")

        items = raw.get("rules", [])
        if not isinstance(items, list):
            raise ValueError("rule pack 'rules' must be a list")

        rules: list[PatternRule] = []
        seen_codes: set[str] = set()
        for item in items:
            if not isinstance(item, dict):
                raise ValueError("each rule must be an object")
            rule = PatternRule(
                code=str(item["code"]),
                pattern=str(item["pattern"]),
                severity=GateDecision(str(item["severity"])),
                message=str(item["message"]),
                remediation=str(item["remediation"]),
            )
            if rule.code in seen_codes:
                raise ValueError(f"duplicate rule code: {rule.code}")
            rule.compile()
            seen_codes.add(rule.code)
            rules.append(rule)

        return cls(name=name, version=version, rules=tuple(rules))


def load_rule_pack(path: Path) -> RulePack:
    raw = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(raw, dict):
        raise ValueError("rule pack must be a JSON object")
    return RulePack.from_dict(raw)


DEFAULT_RULE_PACK = RulePack(
    name="oakgate-core",
    version="0.2.0",
    rules=(
        PatternRule(
            "OAK-OVERCLAIM-ABSOLUTE",
            r"\bpreuve absolue\b",
            GateDecision.BLOCK,
            "Absolute proof language detected.",
            "Replace it with the strongest evidence-bounded status.",
        ),
        PatternRule(
            "OAK-OVERCLAIM-CONSENSUS",
            r"\b100\s*%\s+(?:de\s+)?(?:consensus|approbation|gratitude)\b",
            GateDecision.BLOCK,
            "Universal-consensus language detected without a measured sample.",
            "Report the observed sample size, population, method, and uncertainty.",
        ),
        PatternRule(
            "OAK-OVERCLAIM-CONTROL",
            r"\b(?:contr[oô]le|commande|reprogramme)\s+(?:l['’])?(?:univers|omnivers|humanit[eé]|ga[iï]a)\b",
            GateDecision.BLOCK,
            "Reality-level control claim detected without an operational boundary.",
            "Downgrade to MythOS or define and measure a bounded subsystem.",
        ),
        PatternRule(
            "OAK-PUBLICATION-IRREVERSIBLE",
            r"\b(?:publication|gravure|incrustation)\s+irr[eé]versible\b",
            GateDecision.BLOCK,
            "Irreversible-publication language conflicts with correction and retraction.",
            "Use versioned, reviewable, retractable publication states.",
        ),
        PatternRule(
            "OAK-PHYSICS-CONSTANT",
            r"\bremplace\s+(?:la\s+)?constante\b",
            GateDecision.BLOCK,
            "A physical-law replacement claim requires derivation and evidence.",
            "Remove the claim or provide a formal derivation, domain, units, and tests.",
        ),
        PatternRule(
            "OAK-EXTRATERRESTRIAL-CONFIRMATION",
            r"\bextraterrestres?\s+(?:confirm[eé]s?|int[eé]gr[eé]s?|soumis)\b",
            GateDecision.BLOCK,
            "Extraterrestrial confirmation is asserted without independent verification.",
            "Mark it speculative or attach independently verified evidence.",
        ),
        PatternRule(
            "OAK-THERMO-ZERO-ENTROPY",
            r"\b(?:aucune|z[eé]ro)\s+entropie\b",
            GateDecision.BLOCK,
            "Zero-entropy language lacks a bounded thermodynamic accounting.",
            "Define the system boundary and report entropy production and uncertainty.",
        ),
        PatternRule(
            "OAK-GUARANTEE-REVENUE",
            r"\b(?:revenu|profit|rendement)\s+garanti\b",
            GateDecision.BLOCK,
            "Guaranteed financial outcome detected.",
            "Use a scenario, measured traction, costs, and explicit uncertainty.",
        ),
        PatternRule(
            "OAK-FREE-ENERGY",
            r"\b(?:[eé]nergie\s+gratuite|rendement\s+sup[eé]rieur\s+[àa]\s+100\s*%)\b",
            GateDecision.BLOCK,
            "Free-energy or unbounded-efficiency language detected.",
            "Provide a complete energy balance or remove the claim.",
        ),
    ),
)
