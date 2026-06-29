# Omega Absorb Poly Prof v1.6

Status: local routing and bundle upgrade.

## Purpose

v1.6 adds local record routing, source policy checks, JSON ingestion v2, action packet writing and local GitHub work bundle writing.

```text
records
-> adapter router
-> source policy
-> ingestion v2
-> top actions
-> action packets
-> work bundle
```

## New modules

- `adapter_router.py`
- `source_oak_policy.py`
- `ingest_json_pipeline_v2.py`
- `action_packet_writer.py`
- `github_work_bundle.py`

## CLI commands

```bash
omega-absorb route-source --input records.json
omega-absorb policy-check --input records.json
omega-absorb ingest-json-v2 --input records.json
omega-absorb write-actions --source combined
omega-absorb github-bundle --source combined
```

## Tests

```bash
python examples/omega_absorb_poly_prof_v16_demo.py
python -m pytest tests/test_omega_absorb_poly_prof_v16.py
```

## v1.7 next targets

1. weighted ProfessorTensor;
2. PolyResearchTwin v3;
3. twin answer engine;
4. department strategy matrix;
5. route confidence dashboard.
