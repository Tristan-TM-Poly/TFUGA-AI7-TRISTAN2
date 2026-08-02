# OAKGate R0.2 Max

Status: executable local guardrail; not external scientific, legal, privacy, patent, security, or deployment certification.

## Purpose

OAKGate converts epistemic discipline into a dependency-free Python tool. It evaluates structured claims before publication, productization, investor communication, scientific promotion, or autonomous-agent action.

```text
claim -> structure gates -> rule pack -> U² confidence debt -> provenance -> report
```

## Evidence ladder

```text
M0 Myth
C1 Concept
F2 Formalization
S3 Simulation
P4 Prototype
E5 Empirical result
R6 Reproduced result
T7 Certified/proved result
D8 Measured deployment
```

No status promotion is automatic. A passing report means only that the deterministic rules did not detect a configured failure.

## R0.2 additions

- configurable JSON rule packs;
- Markdown `oak-claim` fenced blocks;
- exact source file and line ranges;
- recursive multi-file scanning;
- canonical SHA-256 provenance hashes;
- provenance mismatch detection;
- U² confidence-debt heuristic;
- public/non-public IP conflict detection;
- SARIF 2.1.0 output;
- GitHub workflow annotations;
- JSON, Markdown, SARIF, and GitHub renderers;
- adversarial and end-to-end tests.

## Claim format

```json
{
  "claim_id": "EXAMPLE-001",
  "text": "A bounded statement.",
  "status": "F2",
  "layer": "TheoryOS",
  "evidence": ["docs/protocol.md"],
  "artifacts": [],
  "uncertainty": 0.35,
  "risks": ["false_positive"],
  "ip_classification": "OPEN_SOURCE",
  "public_intent": true,
  "source_attributions": [],
  "provenance_hash": null
}
```

## Markdown format

````markdown
```oak-claim
{
  "claim_id": "MD-001",
  "text": "A claim embedded in a readable document.",
  "status": "F2",
  "layer": "TheoryOS",
  "evidence": ["docs/design.md"],
  "artifacts": [],
  "uncertainty": 0.4,
  "risks": [],
  "ip_classification": "OPEN_SOURCE",
  "public_intent": false,
  "source_attributions": []
}
```
````

## Commands

```bash
python -m oakgate.cli scan examples/oakgate_claim.json
python -m oakgate.cli scan examples/oakgate_claims.md --format json
python -m oakgate.cli scan examples/oakgate_claims.md --format sarif --output reports/oakgate.sarif
python -m oakgate.cli scan examples/oakgate_claims.md --format github
python -m oakgate.cli scan docs --recursive
python -m oakgate.cli scan claim.json --rules rules/oakgate.deeptech.json
python -m oakgate.cli hash claim.json --output reports/provenance.json
```

Exit codes:

```text
0 PASS
1 WARN
2 BLOCK
3 invalid input or configuration
```

## U² confidence debt

Claimed confidence is interpreted as `1 - uncertainty`. OAKGate compares it with a conservative cap associated with the declared epistemic status. Missing evidence, artifacts, or attribution support lowers the cap.

```text
confidence debt = max(0, claimed confidence - justified cap)
```

This is a transparent policy heuristic. It is not a calibrated probability that a claim is true.

## Provenance

The `hash` command canonicalizes the claim as sorted compact JSON, excludes `provenance_hash`, and computes SHA-256.

```text
sha256:<64 lowercase hexadecimal characters>
```

If a supplied hash no longer matches the claim, OAKGate blocks promotion until the reviewed claim is re-hashed.

## Rule packs

A rule pack defines a name, version, and regex-based findings:

```json
{
  "name": "project-policy",
  "version": "1.0",
  "rules": [
    {
      "code": "PROJECT-001",
      "pattern": "autonomous final decision",
      "severity": "BLOCK",
      "message": "Human authority was bypassed.",
      "remediation": "Require explicit human approval."
    }
  ]
}
```

Custom rule packs replace the default textual pattern pack for that scan. Structural evidence, artifact, IP, privacy, provenance, layer, and U² gates remain active.

## OAK boundaries

OAKGate does not establish:

- truth;
- scientific reproducibility;
- legal patentability;
- regulatory compliance;
- privacy-law compliance;
- cybersecurity certification;
- institutional approval;
- successful publication or deployment;
- guaranteed revenue.

It creates a falsifiable, reviewable, versioned guardrail that makes unsupported promotion harder and failures easier to locate.

## Promotion route

```text
Capture -> private claim -> OAKGate -> human review -> experiment/test
-> IPGate -> versioned publication -> measured deployment -> M⁻ update
```

## Next gates

- domain-specific parsers beyond JSON fenced blocks;
- evidence-file existence checks;
- signed manifests;
- baseline and experiment-result adapters;
- GitHub PR changed-file filtering;
- configurable U² policy profiles;
- false-positive benchmark corpus;
- optional code-scanning SARIF upload after repository security review.
