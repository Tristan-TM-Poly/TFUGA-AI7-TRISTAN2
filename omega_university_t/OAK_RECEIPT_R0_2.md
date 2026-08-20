# Ω-TRISTAN-OMNIUNIVERSITY-SELFGENESIS-T∞ — OAK Receipt R0.2

Status: **candidate pending exact-head CI and review**.

## Delta from R0.1

R0.1 compiles deterministic prerequisite plans only. R0.2 adds three bounded layers:

1. **Capability Evidence Court** — checks caller-supplied evidence against an explicit policy.
2. **Curriculum MIN/NONE Court** — compares structural plan length and declared cost while forcing `NONE` as a baseline.
3. **Research Frontier Bridge** — measures missing declared capabilities for caller-supplied frontier items.

## Claims permitted by this receipt

- the software can deterministically evaluate the declared policy fields implemented in `evidence_ir.py`;
- duplicate evidence IDs and mixed-capability evidence fail closed;
- independent-source counts deduplicate by `source_id`;
- invalid evidence does not contribute to sufficiency;
- curriculum option comparison always includes `NONE`;
- curriculum ranking is deterministic over `(missing_count, declared_cost, option_name)`;
- frontier distance is the number of missing declared prerequisite capabilities;
- all three layers remain non-authorizing.

## Claims explicitly NOT permitted

```text
EvidenceSufficientUnderPolicy != ExternalTruth
Evidence != ScientificProof
Assessment != Credential
ShorterPlan != BetterLearning
SelectedOption != ExecuteOption
ReachableFrontier != OpenProblemVerified
ReachableFrontier != Novelty
ReachableFrontier != ResearchSuccess
SoftwarePASS != EducationalEffectiveness
LocalPASS != GlobalPASS
```

## Reality / evidence boundary

`EvidenceRecord.valid`, `independent`, `source_id`, `method`, and `reality_level` are caller-supplied metadata in R0.2. The kernel does not independently authenticate a laboratory, reproduce a measurement, inspect an artifact, or establish causal learning gain.

Therefore `EVIDENCE_SUFFICIENT_UNDER_POLICY` means exactly that the supplied records satisfy the supplied deterministic policy. Nothing stronger.

## Mandatory NONE baseline

The curriculum court always materializes `NONE`, representing no added declared capability option. A candidate can win only according to the narrow structural ranking implemented in code. This is not an educational recommendation engine.

## Frontier boundary

A `FrontierItem` is caller-supplied. The mapper does not establish that the item is genuinely unsolved, scientifically valuable, safe, legal, fundable, or novel.

## M⁻ encoded

- counting duplicated evidence as independent proof;
- counting invalid records toward sufficiency;
- equating one source with multiple independent sources;
- optimizing without a no-action baseline;
- interpreting graph reachability as scientific contribution;
- granting credentials or external-action authority from software receipts.

## Replay

```bash
python -m unittest discover -s omega_university_t/tests -p 'test_university*.py' -v
```

Promotion requires the exact R0.2 head to pass its own CI and remain a clean stack on the exact R0.1 head. Independent educational benchmarking remains future evidence debt.
