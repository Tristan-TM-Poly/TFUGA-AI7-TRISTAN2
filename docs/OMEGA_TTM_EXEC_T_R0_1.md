# Ω-TTM-EXEC-T R0.1

TTM-EXEC turns the TTM-2048 engineering conclusion into a small executable convergence layer.

## REUSE before CREATE

R0.1 reuses three objects already on `main`:

```text
omega_intent_t.WorkUnit
→ omega_capability_os_t
→ omega_cognitive_computer_t
→ TTM composite receipt
```

It does not define another WorkUnit, capability ontology, or Cognitive ISA. The 17 TTM primitive names are compatibility labels mapped to those existing layers.

## R0.1 contracts

- `compile_report`: canonical WorkUnit → capability plan + cognitive program + GO MAX/MIN selection report.
- `execute_report`: bounded capability run → receipt + residuals + M+/M-/M? + OAK status.
- epistemic compatibility checks keep declared status aligned with declared evidence.
- exact freshness barrier: a completed run remains `HOLD` unless candidate and evidence SHA match exactly.

`PASS` is intentionally narrow. It covers declared execution, exact evidence freshness, and structural claim/evidence compatibility.

## Test court

Focused tests cover primitive reuse, canonical WorkUnit compilation, comparison baselines, exact-SHA freshness and composite receipts.

## Next stage: TTMBench

Compare shared WorkUnits across direct baseline, Capability OS alone, Cognitive Computer + Capability OS, and TTM-EXEC. Measure success, cost, latency, complexity, reuse, failure rate, human intervention and reproducibility. Any layer that does not improve the Pareto frontier becomes a GO MIN candidate.
