# Omega MGHFM TGNT Prime Tensor — Executable Layer

Status: preserved executable layer from PR #9 during zero-manual conflict synthesis.

This document preserves the PR branch enrichment that was originally embedded in `docs/omega-mghfm-tgnt-prime-tensors.md`. It is separated to remove the add/add conflict with `main` while keeping the executable prototype knowledge intact.

## Backed prototype

The prime tensor definitions are backed by a stdlib-only prototype:

- `sage_tristan/prime_tensors.py`
- `tests/test_prime_tensors.py`
- `examples/prime_tensor_demo.py`
- `reports/prime_tensor_oak_report.md`

## Local validation before push

```bash
PYTHONPATH=/tmp python -m unittest test_prime_tensors.py
PYTHONPATH=/tmp python -m sage_tristan.prime_tensors --count 6 --max-jump 2 > /tmp/packet.json
python -m json.tool /tmp/packet.json
```

Recorded branch result: 5 tests passed and the JSON OAK packet was valid.

## Relationship to the canon scaffold

The main canon file remains:

```text
docs/omega-mghfm-tgnt-prime-tensors.md
```

This executable-layer file adds implementation/test provenance without changing the canonical definitions during conflict resolution.

## OAK preservation rule

```text
When a canon conflict appears, preserve executable enrichments in a named layer, realign the shared canon path to main, then re-check mergeability and tests.
```

## Next implementation files

- `sage_tristan/hgfm_prime_graph.py`
- `schemas/prime_tensor_packet.schema.json`
- `reports/prime_tensor_oak_report.md`

## M⁻ memory

Do not solve add/add canon conflicts by blind overwrite. Preserve branch-specific executable content in an explicit layer before realigning the contested path.
