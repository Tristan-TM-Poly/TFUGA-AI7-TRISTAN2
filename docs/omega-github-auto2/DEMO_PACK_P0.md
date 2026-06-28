# Omega AUTO2 Demo Pack P0

Demo Pack P0 turns the current AUTO2 P0 spine into a stable synthetic before/after report.

## Added files

- `fixtures/omega_auto2/demo_pack/demo_request.json`
- `scripts/omega_auto2_demo_pack_p0.py`
- `tests/test_omega_auto2_demo_pack_p0.py`

## Flow

```text
synthetic demo request
→ run_p0_pipeline
→ spectral cleaning result
→ before/after arrays
→ OAK disclaimer
→ JSON demo report
```

## Report fields

- `demo_id`
- `oak_status`
- `request_id`
- `spectrum_id`
- `summary`
- `before_after`
- `module_statuses`
- `residue_report`
- `oak_disclaimer`
- `generated_at`

## OAK disclaimer

The demo report explicitly states:

- synthetic only
- external actions disabled
- production use disabled
- customer data disabled
- no scientific or regulatory claim
- no commercial claim

## CI

The global P0 CI now runs:

```bash
python -m unittest tests/test_omega_auto2_demo_pack_p0.py
python scripts/omega_auto2_demo_pack_p0.py --output artifacts/omega_auto2/demo_pack_p0_report.json
```

## Next action

After this P0 demo pack, the next useful step is a review pack with Markdown rendering and a stable human-readable report.
