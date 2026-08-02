# OAKGate Markdown claim example

The prose around a claim remains readable. OAKGate only evaluates fenced
`oak-claim` JSON objects and preserves their source line range.

```oak-claim
{
  "claim_id": "OAK-R0.2-EXAMPLE-001",
  "text": "OAKGate R0.2 parses bounded JSON claims embedded in Markdown and emits deterministic local findings.",
  "status": "F2",
  "layer": "TheoryOS",
  "evidence": [
    "docs/OAKGATE_R0_2.md",
    "tests/test_oakgate_max.py"
  ],
  "artifacts": [],
  "uncertainty": 0.35,
  "risks": [
    "false_positive",
    "rule_pack_drift"
  ],
  "ip_classification": "OPEN_SOURCE",
  "public_intent": true,
  "source_attributions": []
}
```

This is a formalized software claim, not an external scientific certification.
