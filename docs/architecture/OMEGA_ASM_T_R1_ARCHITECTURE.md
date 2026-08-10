# Ω-ASM-T∞ R1 — Architecture

## Dataflow

```text
JSON / built-in kernel
  -> ASM-IR validator
  -> dependency DAG
  -> static analyzers
  -> ASM-CVCD signature
  -> versioned P2 cost profiles
  -> bounded Pareto tournament
  -> OAK report
  -> human review
```

Native evidence is a separate branch:

```text
trusted built-in x86-64 assembly
  + uint64_t C reference
  -> compiler/assembler
  -> deterministic differential harness (P3)
  -> observational timing + machine manifest (P4)
  -> CI evidence
```

## Modules

| Module | Responsibility |
|---|---|
| `models.py` | immutable typed contracts |
| `ir.py` | JSON conversion, adversarial SSA validation, dot block fixture |
| `analysis.py` | dependencies, critical path, ILP bound, input-aware register lifetime, branch entropy, CVCD |
| `backends.py` | trusted x86-64 and AArch64 built-in emitters |
| `cost_model.py` | versioned, explicitly uncalibrated P2 ordinal cost profiles |
| `search.py` | bounded candidates and strict Pareto dominance |
| `benchmark.py` | robust P4 statistics and execution-context manifest |
| `oak.py` | validated claim/limitation separation and authority gate |
| `cli.py` | stable command-line surface |

## IR trust boundary

The `#` prefix is reserved for immediate values. Program inputs, instruction outputs and program outputs must therefore be ordinary non-empty identifiers. Inputs must be unique.

The validator rejects:

- undefined SSA inputs;
- duplicate SSA definitions;
- duplicate program inputs;
- reserved-prefix identifiers;
- empty operations or identifiers;
- non-finite or negative latency;
- negative/non-integer byte counts;
- non-positive/non-integer vector widths;
- non-finite or out-of-range branch probabilities;
- malformed metadata;
- undefined program outputs.

Public analysis/report entry points validate direct `Program` objects. OAK cannot claim structural validity for an object that has bypassed JSON parsing.

## Register-Time Volume

The liveness proxy includes program inputs with conceptual birth time `-1`, before instruction zero. This prevents function arguments from disappearing from register-pressure estimates.

It remains a structural SSA proxy rather than a physical register allocator: destructive instructions, ABI register classes, spills, renaming and microarchitectural dependencies are future layers.

## Trust boundaries for native execution

R1 does **not** accept arbitrary assembly and execute it. Native CI executes only repository-controlled fixtures under `examples/native/`.

The generated AArch64 backend is not executed on the default CI runner. x86-64 native equivalence is tested, not formally proven.

## Reproducibility

- deterministic IR serialization;
- no network dependency at runtime;
- deterministic native correctness fixtures;
- deterministic benchmark inputs;
- explicit P2 model IDs and calibration state;
- robust P4 distribution summaries;
- execution-context manifest;
- GitHub Actions permissions `contents: read`;
- compiler warnings promoted to errors for native C harnesses;
- generated and checked-in x86 fixture compared by Python tests.

## Performance evidence ladder

```text
P0 semantic specification
P1 static structural metrics
P2 versioned static heuristic ranking
P3 native correctness test
P4 observational timing on one execution context
P5 hardware-counter profile
P6 replicated target-machine benchmark
P7 formally verified transformation/certificate
```

R1 reaches P3 for the built-in x86-64 integer dot-product fixture and includes a P4 observational protocol. P4 numbers are not promoted to universal speed claims and do not gate CI on which implementation wins.
