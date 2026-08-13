# Ω-TENSOR-RISK-GATE-T — R0.6.1

## Status

**Executable software-policy hardening.**

R0.6 filtered candidate LLMTs by checking each member's declared risk against
`ProblemGenome.risk_budget`.  That does not constrain total coalition risk.
R0.6.1 closes that specific loophole with a cumulative additive gate.

## Core rule

Before adding candidate `i`:

```text
cumulative_risk + risk_i <= risk_budget
```

Otherwise the candidate is not admissible in the current coalition.

This addresses:

```text
per-agent risk gate != coalition risk budget
```

## Deliberate limitation

The current aggregation model is:

```text
additive_declared_proxy
```

It does **not** claim:

- statistical independence of risks;
- real-world hazard quantification;
- optimal portfolio allocation;
- correlated-tail-risk modeling;
- physical, legal or safety certification.

The receipt therefore permanently reports:

```text
portfolio_risk_optimality_proven = false
risk_independence_assumed = false
real_world_safety_certified = false
```

## Negative control

The deterministic fixture contains two synthetic LLMTs:

```text
risk_a = 0.30
risk_b = 0.30
budget = 0.50
```

Both are individually below the budget. They cannot coexist under the
cumulative gate. The compiler selects one and leaves one required capability
explicitly uncovered rather than silently violating the risk budget.

This encodes the M- rule:

```text
individual admissibility does not imply coalition admissibility
```

## Standard fixture compatibility

The original R0.6 synthetic routing fixture still selects:

```text
person_a + person_b
```

because its cumulative declared risk is `0.10` under a `0.50` budget.

## Relationship to R0.7

Tensor DiscoveryBench should evaluate the cumulative-risk compiler when
benchmarking adaptive MetaLLMT routing. Otherwise the benchmark would knowingly
measure a router with a closed but bypassed risk contract.

## OAK acceptance gates

R0.6.1 is promotable only if:

1. Python 3.10-3.13 compile/tests pass;
2. standard A+B routing remains admissible;
3. the 0.30+0.30 under 0.50 fixture selects at most one member;
4. cumulative risk never exceeds the declared budget;
5. uncovered capabilities remain visible;
6. no portfolio-risk optimality, independence or safety claim is emitted.

## Future extension

A later version may replace the additive proxy by declared correlation or
scenario-aware risk tensors. That would be a new model requiring its own
benchmarks; it must not be smuggled into the current scalar risk field.
