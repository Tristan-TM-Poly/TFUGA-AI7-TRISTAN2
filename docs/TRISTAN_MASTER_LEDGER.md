# TRISTAN_MASTER_LEDGER

Status: v0.1 — OAK-safe production ledger.

## Law

Every idea must pay tax to reality: definition, file, test, benchmark, limit, residue, revenue path, or canon update.

## Priority board

| Branch | Status | Priority | Risk | Potential | Next artifact |
|---|---:|---:|---:|---:|---|
| Ω-CS-SOFTWARE-TRUTH | B→C | 1 | Low/Medium | Very high | `omega_software_truth/` MVP |
| Ω-ROSETTE-T | B→C | 2 | Medium/IP | Very high | PDF→claims manifest |
| Ω-DRIVE-GITHUB-ABSORB-T | B | 3 | Medium/permissions | Very high | dry-run Drive→GitHub manifest |
| Ω-VTP / TensorProdLift | B→C | 4 | Low | High | exact polynomial lift demo |
| Ω-FFWT-HAC-CVCD | C | 5 | Low | High | benchmark versus FWT/FFT/SVD |
| Ω-REVENUS-T | B | 6 | Low | Very high | micro-offer catalog |
| Ω-ACTION-EXT-T | B | 7 | High | Very high | action manifest + rollback |
| Ω-OAK-SEARCH / EvidenceGraph | B | 8 | Medium | Very high | source/claim/evidence schema |

## Active sprint

### Sprint 1 — Ω-CS-SOFTWARE-TRUTH

Goal: move from doctrine to executable prototype.

Required artifacts:

- `omega_software_truth/software_state.py`
- `omega_software_truth/contracts.py`
- `omega_software_truth/oak_validator.py`
- `omega_software_truth/mutation_probe.py`
- `tests/test_omega_software_truth.py`
- `examples/omega_software_truth_demo.py`
- `docs/m_minus/omega_software_truth.md`

Acceptance criteria:

- A Python callable is represented as a `SoftwareState`.
- Input and output contracts are executable.
- The validator emits an OAK report with verdict and residues.
- A deliberate mutant can be killed by examples.
- No merge to `main` until CI or local test evidence is recorded.

## M⁻ global

- A name is not a proof.
- A prototype passing once is not robustness.
- Zero-touch removes friction; it does not remove responsibility.
- A branch that never produces an artifact becomes cognitive debt.
