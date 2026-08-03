# Ω-CODE-DOJO-T∞ R0.2 Command Atlas

## Inspect the frontier

```bash
omega-code-dojo-r02 frontier --sample 4
```

Returns axis cardinalities, logical cell count and a finite address sample.

## Run an uncapped architecture campaign

```bash
omega-code-dojo-r02 campaign --budget 32
```

The campaign has a finite local budget. The architecture has no permanent total cap.

## Demonstrate an explicit cap

```bash
omega-code-dojo-r02 campaign --budget 32 --permanent-cap 8
```

This is an intentionally constrained experiment, not the default architecture.

## Produce deterministic evidence

```bash
omega-code-dojo-r02 benchmark --budget 32 --output benchmark.json
omega-code-dojo-r02 benchmark --budget 32 --output benchmark-again.json
cmp benchmark.json benchmark-again.json
```

## Python API

```python
from omega_code_dojo_t.r02.benchmark import fixture_provenance
from omega_code_dojo_t.r02.campaign import CampaignEngine
from omega_code_dojo_t.r02.models import CampaignPolicy

receipt = CampaignEngine().run(
    CampaignPolicy(materialization_budget=128),
    fixture_provenance(),
)
assert receipt.permanent_total_cap is None
```

## Extend the frontier

```python
from omega_code_dojo_t.r02.frontier import DEFAULT_FRONTIER

extended = DEFAULT_FRONTIER.extended(
    {
        "domains": ("quantum_algorithms", "symbolic_physics"),
        "languages": ("zig", "ocaml"),
    }
)
assert extended.logical_cell_count > DEFAULT_FRONTIER.logical_cell_count
```

## OAK interpretation

- `logical_frontier_cells`: addressable experiments, not executed experiments;
- `materialized_cells`: generated during this campaign;
- `allocated_units`: deterministic software cost units, not money or energy measurements;
- `receipt_sha256`: integrity checksum, not external certification;
- `CERTIFIED_SOFTWARE_RESEARCH_FIXTURES_R0_2`: internal fixture status only.
