# Ω-UNIVERSAL-RESEARCH-ABI-T∞ — R0.2

R0.2 closes two concrete residuals left by R0.1 while preserving the reuse-first architecture.

## 1. Native bridge to Ω-GITHUB-CUMULATIVE-MEMORY R0.3→R0.7

Because #448 is stacked directly on #447, R0.2 no longer treats the new GitHub-memory evolution objects as generic snapshots.

It reuses their existing ontology and maps them through explicit graph boundaries:

```text
ResidualArtifactSpec
→ G_W / residual_artifact_spec

ReuseOutcomeReceipt
→ G_E / reuse_outcome_receipt

TemporalSupersessionMiner report
→ G_P / supersession_candidate_report / OAK=HOLD

LLMTFederationCompiler receipt
→ G_W / llmt_federation / authority=draft
```

The bridge never changes the meaning of the upstream fields.

Hard boundaries remain:

```text
generation_allowed != GitHub write authority
reuse outcome != causal proof
merge state != M+
inferred supersession != strong lineage
LLMT packet count != independent evidence
logical LLMT identity != independent mind/person
```

## 2. Research Transition Ledger

R0.1 introduced `TransformationReceipt`. R0.2 chains valid receipts through state transitions:

```text
S0
-- Receipt(T0) --> S1
-- Receipt(T1) --> S2
-- Receipt(T2) --> ...
```

Each `TransitionLedgerEntry` stores:

```text
index
previous_hash
receipt_id
receipt_fingerprint
state_before
state_after
chain_hash
```

with:

```text
chain_hash_i = H(index_i,
                 previous_hash_i,
                 receipt_id_i,
                 receipt_fingerprint_i,
                 state_before_i,
                 state_after_i)
```

The verifier checks:

- sequential indices;
- previous-hash continuity;
- state continuity (`state_after[i-1] == state_before[i]`);
- recomputed chain hashes.

The ledger is append-only **by contract**, not by Python memory protection. `verify()` detects mutation relative to the hash chain; it does not replace signed Git commits, independent timestamping, external audit or theorem proving.

```text
hash-chain integrity != external truth
receipt validity != semantic correctness
```

## 3. Compiler integration

`ResearchABICompiler.transform()` now optionally accepts:

```text
state_before
state_after
```

Both must be provided together. A valid receipt is appended to the transition ledger and returned with its `ledger_entry`.

`compile()` now emits:

```text
graph_validation
bounded context
receipts
transition_ledger
component_manifest
OAK boundaries
fingerprint
```

The reference fixture therefore exercises the closed transition:

```text
state:reuse-memory-r07
→ compile_universal_research_abi
→ state:universal-research-abi-r02
```

## 4. Cumulative loop

The direct composition of #447 + #448 now supports:

```text
all PR memory
→ ReuseBeforeCreate
→ residual implementation contract
→ bounded LLMT federation
→ typed research objects
→ transformation
→ receipt
→ transition ledger
→ exact-head evidence
→ ReuseOutcomeReceipt
→ M+ / M- / M?
→ future reuse policy
```

This is still an engineering/research architecture. The presence of a closed software loop does not establish autonomous scientific discovery, causal learning, or general intelligence.

## 5. Deterministic R0.2 court

```bash
python -m compileall -q omega_research_abi_t
pytest -q tests/test_omega_research_abi_t.py tests/test_omega_research_abi_r02.py
python -m omega_research_abi_t examples/research_abi_fixture.json --compact
```

The R0.2 court verifies:

1. native structural reuse of `ResidualArtifactSpec`;
2. no write-authority widening;
3. evidence-bearing `ReuseOutcomeReceipt` → Experiment mapping;
4. preservation of M+/M-/M? without causal promotion;
5. supersession review candidates remain `OAK=HOLD`;
6. LLMT federation remains `draft` authority;
7. valid two-step hash-chain continuity;
8. tampering detection;
9. state-continuity violation detection;
10. end-to-end fixture ledger emission.

## 6. Next integration frontier

The remaining independent PRs #443–#446 should stay snapshot adapters until intentionally co-resident. Once they are stacked/merged, the same pattern should replace each generic bridge with native adapters and specialized receipts rather than copying their models.

Priority residuals:

```text
#444 Discovery OS
→ ClaimCertificate / ScientificBuildGraph / TheoryDiffReceipt

#446 Cognitive Computer
→ CIR / CognitiveProgram / obligation receipts

#445 Compute Physics
→ Snapshot / ComplexityIR / BenchmarkContract / OptimizationGene

#443 GreatSages/Tensor Research
→ DiscoveryPath / representation morphism / coalition receipts
```

The invariant remains:

```text
REUSE EXISTING ONTOLOGY
→ ADD THE SMALLEST TYPED BRIDGE
→ EMIT RECEIPTS
→ TEST EXACT HEAD
→ LEARN ONLY FROM EVIDENCE-BEARING OUTCOMES
```
