from __future__ import annotations

import json

from oakgate import (
    Claim,
    EpistemicLayer,
    EpistemicStatus,
    GateDecision,
    claim_provenance_hash,
    evaluate_claim,
)
from oakgate.cli import main
from oakgate.config import load_rule_pack
from oakgate.sarif import reports_to_sarif
from oakgate.scanner import load_scanned_claims


def _passing_claim() -> Claim:
    return Claim(
        claim_id="MAX-PASS-001",
        text="OAKGate parses bounded claims and emits deterministic local findings.",
        status=EpistemicStatus.FORMALIZATION,
        layer=EpistemicLayer.THEORY,
        evidence=["tests/test_oakgate_max.py"],
        uncertainty=0.35,
        ip_classification="OPEN_SOURCE",
    )


def test_custom_rule_pack_blocks_project_specific_language(tmp_path) -> None:
    rules = tmp_path / "rules.json"
    rules.write_text(
        json.dumps(
            {
                "name": "project-safe",
                "version": "1",
                "rules": [
                    {
                        "code": "CUSTOM-001",
                        "pattern": "autonomous final decision",
                        "severity": "BLOCK",
                        "message": "Human authority was bypassed.",
                        "remediation": "Require explicit human approval.",
                    }
                ],
            }
        ),
        encoding="utf-8",
    )
    pack = load_rule_pack(rules)
    claim = _passing_claim()
    claim.text = "This system makes an autonomous final decision."

    report = evaluate_claim(claim, rule_pack=pack)

    assert report.decision is GateDecision.BLOCK
    assert report.findings[0].code == "CUSTOM-001"


def test_markdown_scanner_preserves_line_location(tmp_path) -> None:
    path = tmp_path / "claims.md"
    path.write_text(
        """# Claims

Some prose.

```oak-claim
{
  "claim_id": "MD-001",
  "text": "Bounded parser implementation.",
  "status": "F2",
  "layer": "TheoryOS",
  "evidence": ["claims.md"],
  "artifacts": [],
  "uncertainty": 0.4,
  "risks": [],
  "ip_classification": "OPEN_SOURCE",
  "public_intent": false,
  "source_attributions": []
}
```
""",
        encoding="utf-8",
    )

    scanned = load_scanned_claims(path)

    assert len(scanned) == 1
    assert scanned[0].claim.claim_id == "MD-001"
    assert scanned[0].source.start_line == 6
    assert scanned[0].source.end_line >= scanned[0].source.start_line


def test_provenance_hash_is_stable_and_mismatch_blocks() -> None:
    claim = _passing_claim()
    digest = claim_provenance_hash(claim)
    assert digest == claim_provenance_hash(claim)

    claim.provenance_hash = "sha256:" + "0" * 64
    report = evaluate_claim(claim)

    assert report.decision is GateDecision.BLOCK
    assert any(item.code == "OAK-PROVENANCE-001" for item in report.findings)


def test_u2_confidence_debt_blocks_overconfident_concept() -> None:
    claim = Claim(
        claim_id="U2-001",
        text="A bounded but early concept.",
        status=EpistemicStatus.CONCEPT,
        layer=EpistemicLayer.THEORY,
        uncertainty=0.0,
        ip_classification="NOT_APPLICABLE",
    )

    report = evaluate_claim(claim)

    assert report.decision is GateDecision.BLOCK
    assert report.confidence_debt >= 0.5
    assert any(item.code == "OAK-U2-DEBT-001" for item in report.findings)


def test_sarif_contains_source_location(tmp_path) -> None:
    path = tmp_path / "claim.json"
    path.write_text(
        json.dumps(
            {
                "claim_id": "SARIF-001",
                "text": "preuve absolue",
                "status": "C1",
                "layer": "TheoryOS",
                "evidence": [],
                "artifacts": [],
                "uncertainty": 0.5,
                "risks": [],
                "ip_classification": "NOT_APPLICABLE",
                "public_intent": False,
                "source_attributions": [],
            }
        ),
        encoding="utf-8",
    )

    scanned = load_scanned_claims(path)[0]
    report = evaluate_claim(scanned.claim, source=scanned.source)
    sarif = reports_to_sarif([report])
    result = sarif["runs"][0]["results"][0]

    assert result["ruleId"] == "OAK-OVERCLAIM-ABSOLUTE"
    assert result["locations"][0]["physicalLocation"]["region"]["startLine"] == 1


def test_cli_hash_and_sarif_outputs(tmp_path) -> None:
    path = tmp_path / "claim.json"
    path.write_text(
        json.dumps(_passing_claim().to_dict()),
        encoding="utf-8",
    )
    hash_output = tmp_path / "hashes.json"
    sarif_output = tmp_path / "report.sarif"

    assert main(["hash", str(path), "--output", str(hash_output)]) == 0
    assert "sha256:" in hash_output.read_text(encoding="utf-8")

    assert (
        main(
            [
                "scan",
                str(path),
                "--format",
                "sarif",
                "--output",
                str(sarif_output),
            ]
        )
        == 0
    )
    payload = json.loads(sarif_output.read_text(encoding="utf-8"))
    assert payload["version"] == "2.1.0"
