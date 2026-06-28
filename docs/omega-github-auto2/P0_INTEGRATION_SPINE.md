# Omega AUTO2 P0 Integration Spine

This PR connects the three merged P0 organs into one offline spine:

- API Gateway P0
- Usage Events P0
- Spectral Core P0

## Package

```text
omega_auto2_p0/
  __init__.py
  oak.py
  pipeline.py
```

## Flow

```text
synthetic request
→ gateway_core
→ spectral_oak_report
→ usage event normalization
→ combined OAK status
→ next action
```

## Shared OAK envelope

`omega_auto2_p0.oak.OAKEnvelope` standardizes:

- `oak_status`
- `errors`
- `warnings`
- `residue_report`
- `external_actions_allowed`
- `production_use_allowed`
- `next_action`

## OAK status

This is still a synthetic/offline P0 integration layer.

It does not:

- call external services
- use customer data
- enable production use
- enable charging or invoicing
- make scientific or regulatory claims

## Test

```bash
python -m unittest tests/test_omega_auto2_p0_integration.py
```

The global P0 CI workflow runs all existing P0 module tests plus the integration test.
