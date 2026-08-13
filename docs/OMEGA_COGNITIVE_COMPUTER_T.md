# Ω-COGNITIVE-COMPUTER-T∞ — v0.1 executable kernel

This module turns reusable problem-solving strategies into an inspectable instruction set rather than a personality imitation.

## Contract

`intent -> Ω-CIR -> problem fingerprint -> cognitive program -> transactional runtime -> OAK/crystallization gates`

The v0.1 kernel is deliberately conservative: generation operators emit **candidates and obligations**, while `PROVE`, `SIMULATE`, `MEASURE`, `BENCHMARK`, and `OAK` never fabricate validation. Domain engines can be attached later through runtime hooks.

## Components

- **Ω-CIR-T**: `CognitiveState` with goals, hypotheses, assumptions, constraints, evidence, uncertainty, representations, provenance, scale, metadata and artifacts.
- **Cognitive ISA**: 30 inspectable opcodes grouped into generation, representation, structure, compression, critique, causal, validation, learning, meta and production categories.
- **Balanced duals**: EXPAND/COMPRESS, ZOOM/DEZOOM, GENERALIZE/SPECIALIZE, MERGE/SPLIT, ABSTRACT/CONCRETIZE, SIMULATE/MEASURE, REMEMBER/FORGET.
- **Cognitive Assembly**: compact text programs (`REP geometric`, `INV`, `ATTACK`, `OAK`, `CRYST`).
- **Compiler**: a v0 heuristic router for mathematics, engineering, empirical science and general/theory problems.
- **Runtime/JIT**: cost budgets, step limits, branch-limit auto-pruning, stagnation-triggered representation diversification, transaction rollback, and explicit operator hooks.
- **M+/M- cache**: stores problem fingerprints, strategies, outcomes and failure modes; nearest-neighbor retrieval returns the strategy, not merely the answer.
- **Representation Market**: allocates exploration budget across competing representations while preserving an exploration floor.
- **Cognitive Algebra**: program composition, declared duals, commutator/order-effect measurement and idempotence distance.
- **Causal Cognitive Profiler**: ablations, exact small-n Shapley attribution and pairwise synergy scores with externally supplied benchmark functions.
- **Meta-Skill Discovery**: mines repeated opcode n-grams from traces as candidates for future superinstructions.
- **Cognitive Evolution**: benchmark-gated dual/drop mutation and crossover scaffold. Fitness is external; self-modification is not treated as improvement by default.
- **Crystallization Compiler 2.0 gate**: requires `spec + implementation + test + baseline + result + provenance + limitations` before an artifact is considered crystallized.

## Canonical superinstructions

- `TRISTAN_EXPLORE`: multi-representation + zoom/dezoom + expansion + transfer.
- `TRISTAN_COMPRESS`: merge + invariants + compression.
- `TRISTAN_ATTACK`: counter-hypotheses + attack + contradiction + residual mining.
- `TRISTAN_CRYSTALLIZE`: concretize + benchmark + OAK + crystallization gate.
- `TRISTAN_DISCOVER`: composition of all four.

## Example

```python
from omega_cognitive_computer_t import CognitiveComputer

computer = CognitiveComputer.default()
program = computer.compile("prove a theorem about polynomial zeros")
result = computer.execute("prove a theorem about polynomial zeros")

print(program.opcodes())
print(result.state.metadata["obligations"])
```

CLI:

```bash
python -m omega_cognitive_computer_t compile "design a multiscale thermal sensor"
python -m omega_cognitive_computer_t run "test a nonlinear physical model" --budget 20
python -m omega_cognitive_computer_t operators
```

## OAK boundary

This package is a **research/prototyping substrate**. A generated hypothesis, analogy, residual pattern, simulation request, or proof obligation is not evidence by itself. `review_ready` only means the local structural audit found no configured blocker; it never means “true” or “proved”. Formal proof requires an external replayable proof checker, and physical/scientific claims require appropriate empirical validation.

## Next integration frontier

The intended adapters are HGFM memory, CVCD compression, Theory Debugger/assumption Jacobians, formal-proof kernels, domain simulators, Evidence Ledger, Research Factory, GitHub Brain and Asset Factory. These should arrive as explicit adapters/hook providers rather than hidden coupling in the core ISA.
