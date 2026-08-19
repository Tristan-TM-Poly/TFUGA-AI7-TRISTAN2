# EvidenceGate V8.3

EvidenceGate is never bypassed. More generation means stricter validation.

## Reality registers

| Register | Meaning |
|---|---|
| R0 | myth, metaphor, vision, fiction, symbolic language |
| R1 | structured concept |
| R2 | mathematical or architectural model |
| R3 | executable local prototype or simulation |
| R4 | measurement, benchmark, or experimental evidence |
| R5 | reproducible proof or independently verified result |

## Rule

```text
Claim(X) <= Evidence(X)
```

## PowerReal

```text
PowerReal(X) in [0, 1]
```

If a score exceeds 1.0, the result is blocked as a normalization error.

## Forbidden promotions

- R0 metaphor -> R5 proof without tests.
- Simulation -> physical validation without measurements.
- Local patch -> external deployment without approval.
- Agent suggestion -> autonomous action without ApprovalSentinel.

## Gate response

```json
{
  "status": "blocked",
  "reason": "Evidence below required register",
  "next": "send_to_redteam_or_add_measurement"
}
```
