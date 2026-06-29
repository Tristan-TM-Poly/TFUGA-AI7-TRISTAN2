# Omega Absorb Poly Prof v1.4

Status: strict schema, ClaimGraph OAK++, method reproduction, M-minus and GitHub packet seed upgrade.

## Purpose

v1.4 strengthens Omega Absorb with stricter source validation, anti-overclaim claim expansion, reproducible method packets, a memory-minus registry of known frictions, and a seed generator for future GitHub work packets.

```text
public/demo records
-> strict source schema
-> ClaimGraph OAK++
-> Method reproduction packets
-> M-minus registry
-> GitHub work packet seed
```

## New modules

- `source_registry_schema.py`: strict source schemas with required, allowed and restricted fields.
- `claim_oak_plus.py`: expands claims into counterclaims, falsification tests and confidence status.
- `method_reproduction_packet.py`: turns methods into reproduction packets with inputs, outputs, assumptions, failures and tests.
- `mminus_registry.py`: canonical memory-minus registry for recurring package and connector frictions.
- `github_packet_generator.py`: local seed generator for implementation/test/doc packets.

## CLI commands

```bash
omega-absorb schema-check --source combined
omega-absorb claim-oak --source combined
omega-absorb method-packets --source combined
omega-absorb mminus
omega-absorb github-packet --feature claim_oak_plus
```

## Generated examples

- `generated/omega_absorb_poly_prof_v14/README.md`
- `generated/omega_absorb_poly_prof_v14/source_schema_report.txt`
- `generated/omega_absorb_poly_prof_v14/claim_oak_plus.md`
- `generated/omega_absorb_poly_prof_v14/method_packets.md`
- `generated/omega_absorb_poly_prof_v14/mminus.md`
- `generated/omega_absorb_poly_prof_v14/github_packet.md`

## Tests

```bash
python examples/omega_absorb_poly_prof_v14_demo.py
python -m pytest tests/test_omega_absorb_poly_prof_v14.py
```

## OAK boundary

- Restricted fields such as secrets, tokens and private identifiers are blocked by schema findings.
- Claims are converted into test seeds, not truth.
- Method packets are reproduction scaffolds, not proof of reproducibility.
- GitHub packets are local work specifications, not external actions by themselves.

## v1.5 next targets

1. ProfessorTensor;
2. PolyResearchTwin v2;
3. department bridge optimizer;
4. top-10 next actions engine;
5. OAK packet manifest.
