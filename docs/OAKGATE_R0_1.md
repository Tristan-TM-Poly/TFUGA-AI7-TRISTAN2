# OAKGate R0.1

**Status:** executable epistemic and publication guardrail. It is not external scientific, legal, patent, or institutional certification.

## Mission

OAKGate converts a strong statement into an inspectable decision:

```text
claim -> status -> evidence -> artifact -> uncertainty -> IP -> privacy -> PASS/WARN/BLOCK
```

The module preserves the creative breadth of TFUGA while preventing narrative, hypothesis, prototype, measurement, and proof from collapsing into one category.

## Four layers

| Layer | Meaning | Typical status |
|---|---|---|
| MythOS | Fiction, metaphor, archetype, narrative design | M0 |
| TheoryOS | Definitions, hypotheses, equations, formal models | C1-F2 |
| PrototypeOS | Simulation, code, demonstrator, local tests | S3-P4 |
| RealityOS | Measurement, reproduction, certification, deployment | E5-D8 |

## Evidence ladder

```text
M0 Myth
C1 Concept
F2 Formalization
S3 Simulation
P4 Prototype
E5 Empirical result
R6 Reproduced result
T7 Certified/proven result
D8 Measured deployment
```

No claim may jump from narrative or concept directly to certification.

## Deterministic gates in R0.1

- evidence required from F2 onward;
- inspectable artifact required from P4 onward;
- zero-uncertainty warning for empirical and deployed claims;
- mandatory IP classification;
- blocking of absolute reality-level language without operational boundaries;
- blocking of claimed external execution without a commit, deployment, log, or other artifact;
- blocking of sensitive birth/family information in public-intent text;
- blocking of external attributions without evidence;
- warning when MythOS content carries a non-myth status.

## CLI

```bash
python -m oakgate.cli scan examples/oakgate_claim.json
python -m oakgate.cli scan examples/oakgate_claim.json --format json
python -m oakgate.cli scan examples/oakgate_claim.json --output reports/oakgate.md
```

Installed entry point:

```bash
oakgate scan examples/oakgate_claim.json
```

Exit codes:

- `0`: PASS
- `1`: WARN
- `2`: BLOCK
- `3`: invalid input or I/O failure

## Claim example

```json
{
  "claim_id": "OAK-DEMO-001",
  "text": "OAKGate classifies claims using deterministic local rules.",
  "status": "F2",
  "layer": "TheoryOS",
  "evidence": ["docs/OAKGATE_R0_1.md"],
  "artifacts": ["oakgate/gates.py"],
  "uncertainty": 0.2,
  "risks": ["rules are heuristic and require human review"],
  "ip_classification": "OPEN_SOURCE",
  "public_intent": true,
  "source_attributions": []
}
```

## Non-claims

OAKGate does not claim that:

- a passing statement is scientifically true;
- a repository artifact proves a physical theory;
- a deterministic rule replaces peer review;
- an IP classification is legal advice;
- privacy detection is exhaustive;
- a deployment or publication occurred without an external execution artifact.

## Next gates

1. add configurable rule packs;
2. add line-level Markdown scanning;
3. add provenance hashes and commit verification;
4. add JSON Schema validation in CI;
5. add calibrated confidence and U² debt;
6. add a GitHub check that annotates overclaims in pull requests;
7. benchmark false-positive and false-negative rates on a labeled claim corpus.
