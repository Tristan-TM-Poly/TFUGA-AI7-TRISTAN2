# Ω-TENSOR-DISCOVERYBENCH-T∞ — R0.7

## Status

**Executable benchmark-harness software model.**

R0.7 exists to falsify and compare the R0.6 Tensor Research Compiler against
simpler baselines.  The deterministic fixtures validate benchmark plumbing and
comparison semantics; they are not measurements of human intelligence, real
scientific discovery productivity, or historical cognition.

The benchmark must be allowed to conclude that a simpler baseline is better.
`MetaLLMT` is never promoted by architectural preference.

## Comparison contract

Every task is evaluated under the same declared task/evidence boundary by four
system classes:

```text
single_llmt
single_shadow
fixed_coalition
meta_llmt
```

R0.7 therefore asks a falsifiable question:

```text
Does adaptive tensor routing add enough measured value to repay its cost?
```

The answer may be no.

## Eight task families

R0.7 defines the benchmark surface:

```text
historical
synthetic
secret
dynamic
formal
simulation
cross_domain
adversarial
```

The current deterministic fixtures provide one task per family.  They test the
harness, not the scientific capabilities of a deployed language model.

## Multi-axis evaluation

R0.7 intentionally avoids a scalar intelligence score.

Each run keeps separate:

- capability coverage;
- evidence-strength proxy;
- calibration proxy;
- robustness proxy;
- verified-information-gain proxy;
- declared resource cost;
- cost-normalized discovery yield;
- contamination tensor.

A Pareto frontier preserves tradeoffs instead of forcing all dimensions into a
single number.

## Discovery yield

The software fixture reports:

```text
discovery_yield = verified_information_gain_proxy / declared_cost
```

`verified` means only "validated inside this deterministic benchmark fixture".
It does not mean scientifically verified in the external world.

`novelty_scope = benchmark_only` is permanent for these fixtures.

## Discovery Contamination Tensor

Contamination is not hidden inside the quality score.

Every task carries:

```text
(context,
 retrieval,
 tools,
 pretraining,
 benchmark,
 human)
```

with categorical exposure status:

```text
controlled_zero
possible
present
unknown
```

A run is eligible even to discuss independent discovery only when all six axes
are `controlled_zero`.

This is deliberately strict.

### Historical tasks

For the historical family, pretraining exposure is `possible` and human
exposure is `unknown` in the deterministic contract.  Therefore historical
rediscovery cannot be promoted as independent discovery merely because context
and retrieval gates were clean.

Permanent M-:

```text
context leakage control != pretrained-memory control
historical rediscovery != independent discovery
```

## Baselines are permanent

R0.7 keeps all four architecture classes in every task.  A future benchmark may
add additional baselines, but MetaLLMT must never be evaluated without simpler
comparators.

The deterministic fixture intentionally permits specialized baselines to beat
MetaLLMT on simple tasks when adaptive routing overhead is not repaid.

Permanent M-:

```text
more agents != more value
meta architecture != automatic superiority
```

## Tensor routing benchmark

`meta_llmt` reuses the sparse R0.6 coalition compiler against each task's
required capabilities.  It therefore tests adaptive membership selection
rather than a fixed A+B coalition.

This does not prove the greedy router globally optimal.

R0.6 already declares:

```text
greedy_heuristic_not_global_optimum = true
full_tensor_materialized = false
```

R0.7 preserves that boundary.

## Ablations

R0.7 generates ablation receipts for the operator-bearing steps in the R0.6
Ceres cognitive-program fixture.

For each removed instruction it records:

```text
baseline capability coverage
ablated capability coverage
delta coverage
```

Every receipt permanently carries:

```text
causal_effect_proven = false
```

Ablation deltas are evidence about a benchmark configuration. They are not by
themselves proof that an operator has a causal effect on scientific discovery.

## Pareto evaluation

For one task, system A dominates B only when it is no worse on every declared
quality axis, no more expensive, and strictly better on at least one quality or
cost dimension.

The result is a set of non-dominated architectures:

```text
ParetoReceipt.frontier_system_ids
```

This prevents one arbitrary coefficient vector from silently becoming an
"intelligence law".

## Current deterministic fixture

The synthetic R0.6 registry is intentionally retained because it makes routing
semantics testable without inventing claims about real historical people.

It contains:

```text
person_a -> representation_switch + invariant_search
person_b -> residual_control + counterexample
person_c -> redundant / expensive representation capability
```

The MetaLLMT router may choose different subsets for different tasks.

These IDs are software fixtures only.

## R0.6 dependency

R0.7 is downstream of the green R0.6 contracts:

```text
PersonLLMT
-> Shadow Factory
-> Sparse Tensor Coalition
-> Cognitive Program
-> R0.5 representation gate
-> R0.4 DiscoveryPath
```

R0.7 does not replace those gates; it compares configurations built on top of
them.

## R0.6.1 debt discovered during OAK review

Current R0.6 `risk_budget` filters each candidate LLMT individually. It does not
yet constrain cumulative coalition risk.

Until a cumulative-risk policy is implemented and benchmarked, R0.7 must not
claim portfolio-risk optimality for the router.

Permanent M-:

```text
per-agent risk gate != coalition risk budget
```

## Machine-readable contract

`schemas/tensor_discovery_bench_r07.schema.json` locks:

- benchmark-family enum;
- system-kind enum;
- contamination axes/statuses;
- run fields;
- `human_novelty_claimed = false`;
- `independent_discovery_claimed = false`;
- `causal_effect_proven = false` for ablations;
- `scalar_intelligence_score_produced = false`;
- `meta_llmt_automatically_superior = false`.

Schema validity proves structure only.

## OAK acceptance gates

R0.7 is promotable as a software benchmark layer only when:

1. Python 3.10–3.13 compile and targeted tests pass;
2. schema/runtime enums and dataclass fields align;
3. all eight benchmark families exist;
4. every task compares all four system kinds;
5. the deterministic suite contains 32 runs;
6. cost remains explicit and normalized yield is reported;
7. contamination remains separate from quality;
8. historical pretraining contamination is not erased;
9. no human novelty or independent-discovery certificate is emitted;
10. ablations remain explicitly non-causal;
11. Pareto fronts do not emit a scalar intelligence score;
12. MetaLLMT superiority is not hard-coded.

## What R0.7 enables next

Once R0.7 is green, R0.8 can begin storing benchmark episodes and estimating:

```text
P(outcome | problem genome, coalition, shadow program, context)
```

with:

- operator/coalition credit;
- Value of Computation;
- M+ / M- / M?;
- ablation/intervention history;
- uncertainty and calibration;
- explicit separation of predictive association from causal evidence.

The next generation is therefore:

```text
Ω-TENSOR-RESEARCH-SELF-MODEL-T∞ — R0.8
```

not a claim of autonomous scientific intelligence.

## Permanent doctrine

```text
benchmark != proof
proxy != natural law
rediscovery != novelty
ablation != causal proof
MetaLLMT != automatic superiority
contamination must remain visible
plus ultra = more falsifiable, not more flattering
```
