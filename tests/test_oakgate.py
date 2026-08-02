from __future__ import annotations

from oakgate import Claim, EpistemicLayer, EpistemicStatus, GateDecision, evaluate_claim
from oakgate.cli import main


def test_blocks_status_inflation_and_unsupported_external_execution() -> None:
    claim = Claim(
        claim_id="OAK-FAIL-001",
        text="HMAGFM² contrôle l'univers et a publié le système.",
        status=EpistemicStatus.CERTIFIED,
        layer=EpistemicLayer.REALITY,
        evidence=[],
        artifacts=[],
        uncertainty=0.0,
        ip_classification=None,
        public_intent=True,
    )

    report = evaluate_claim(claim)
    codes = {finding.code for finding in report.findings}

    assert report.decision is GateDecision.BLOCK
    assert "OAK-EVIDENCE-001" in codes
    assert "OAK-ARTIFACT-001" in codes
    assert "OAK-IP-001" in codes
    assert "OAK-OVERCLAIM-CONTROL" in codes
    assert "OAK-EXECUTION-001" in codes


def test_passes_bounded_formal_claim_with_evidence_and_ip_classification() -> None:
    claim = Claim(
        claim_id="OAK-PASS-001",
        text=(
            "OAKGate is a deterministic software guardrail that classifies "
            "claims and reports missing evidence."
        ),
        status=EpistemicStatus.FORMALIZATION,
        layer=EpistemicLayer.THEORY,
        evidence=["docs/OAKGATE_R0_2.md"],
        artifacts=[],
        uncertainty=0.35,
        ip_classification="OPEN_SOURCE",
    )

    report = evaluate_claim(claim)

    assert report.decision is GateDecision.PASS
    assert report.findings == ()


def test_blocks_sensitive_family_identity_in_public_text() -> None:
    claim = Claim(
        claim_id="OAK-PRIVACY-001",
        text="Tristan est né à Laval le 26 juillet 2000, fils de deux personnes nommées.",
        status=EpistemicStatus.MYTH,
        layer=EpistemicLayer.MYTHOS,
        uncertainty=1.0,
        ip_classification="NOT_APPLICABLE",
        public_intent=True,
    )

    report = evaluate_claim(claim)

    assert report.decision is GateDecision.BLOCK
    assert any(finding.code == "OAK-PRIVACY-001" for finding in report.findings)


def test_warns_when_mythos_is_given_non_myth_status() -> None:
    claim = Claim(
        claim_id="OAK-LAYER-001",
        text="The Singularité Blanche is a narrative design metaphor.",
        status=EpistemicStatus.CONCEPT,
        layer=EpistemicLayer.MYTHOS,
        uncertainty=0.8,
        ip_classification="NOT_APPLICABLE",
    )

    report = evaluate_claim(claim)

    assert report.decision is GateDecision.WARN
    assert any(finding.code == "OAK-LAYER-001" for finding in report.findings)


def test_cli_returns_block_exit_code(tmp_path) -> None:
    input_path = tmp_path / "claim.json"
    input_path.write_text(
        """{
          "claim_id": "CLI-001",
          "text": "Publication irréversible accomplie",
          "status": "D8",
          "layer": "RealityOS",
          "evidence": [],
          "artifacts": [],
          "uncertainty": 0,
          "risks": [],
          "ip_classification": "OPEN_SOURCE",
          "public_intent": false,
          "source_attributions": []
        }""",
        encoding="utf-8",
    )

    assert main(["scan", str(input_path), "--format", "json"]) == 2
