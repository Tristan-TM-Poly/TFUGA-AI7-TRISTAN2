# Ω-ASM-T∞ R1 — Architecture

## Dataflow

```text
JSON / built-in kernel
  -> ASM-IR validator
  -> dependency DAG
  -> static analyzers
  -> ASM-CVCD signature
  -> backend candidates
  -> bounded Pareto tournament
  -> OAK report
  -> human review
```

Native verification is a separate branch of evidence:

```text
trusted built-in x86-64 assembly
  + uint64_t C reference
  -> compiler/assembler
  -> deterministic differential harness
  -> CI evidence
```

## Modules

| Module | Responsibility |
|---|---|
| `models.py` | immutable typed contracts |
| `ir.py` | JSON conversion, SSA validation, dot block fixture |
| `analysis.py` | dependencies, critical path, ILP bound, register lifetime, branch entropy, CVCD |
| `backends.py` | trusted x86-64 and AArch64 built-in emitters |
| `search.py` | bounded candidates, strict Pareto dominance |
| `oak.py` | claim/limitation separation and authority gate |
| `cli.py` | stable command-line surface |

## Trust boundaries

R1 does **not** accept arbitrary assembly and execute it. Native CI executes only repository-controlled fixtures under `examples/native/`.

The generated AArch64 backend is not executed on the default CI runner. x86-64 native equivalence is tested, not formally proven.

## Reproducibility

- deterministic IR serialization;
- no network dependency at runtime;
- no random benchmark claims;
- deterministic xorshift harness seed;
- GitHub Actions permissions `contents: read`;
- compiler warnings promoted to errors for the C harness;
- generated and checked-in x86 fixture compared by Python tests.

## Performance evidence ladder

```text
P0 semantic specification
P1 static structural metrics
P2 static heuristic ranking
P3 native correctness test
P4 controlled timing benchmark
P5 hardware-counter profile
P6 replicated target-machine benchmark
P7 formally verified transformation/certificate
```

R1 reaches P3 for the built-in x86-64 integer dot-product fixture. No higher performance level is claimed.
